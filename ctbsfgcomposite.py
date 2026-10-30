#!/usr/bin/env python3

import os
import sys
import glob
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, RBF
from sklearn.exceptions import ConvergenceWarning
from scipy.optimize import curve_fit
from scipy.stats import chi2 as chi2_dist

warnings.filterwarnings("ignore", category=ConvergenceWarning)
np.seterr(invalid="ignore", divide="ignore")

data_dir = "data"
scheme_csv = "Discrete_Level_Scheme.csv"
cutoff_col_index = 11
k_samples = 50

MIN_VAR = 1e-12
EPS_U = 1e-6
EXP_CLIP = 700.0

# A fit is flagged when the chi2 p-value falls below this threshold:
# p = P(chi2 >= chi2_obs | model correct) = 1 - F_chi2(chi2_obs, dof)
P_VALUE_THRESHOLD = 0.01

gpr_kernel = ConstantKernel(1.0, (1e-3, 1e3)) * RBF(1.0, (1e-2, 1e2))
gpr_restarts = 5
gpr_normalize_y = True

fig_dir = "figs3"
os.makedirs(fig_dir, exist_ok=True)

params_dir = "ct_params"
os.makedirs(params_dir, exist_ok=True)

def within_two_sigma(x0, dx0, xg, dxg):
    return abs(xg - x0) < 2 * np.sqrt((dx0 or 0) ** 2 + dxg ** 2)

def nice_pm(val, err):
    return f"{val:.4f}±{(err if np.isfinite(err) else float('nan')):.4f}"

#BSFG 
def bsfg_density(e, a, delta):
    e = np.asarray(e, dtype=float)
    U = np.maximum(e - float(delta), EPS_U)
    coef = np.sqrt(np.pi) / 12.0
    expo = 2.0 * np.sqrt(np.maximum(a, 1e-12) * U)
    expo = np.clip(expo, -EXP_CLIP, EXP_CLIP)
    return coef * np.exp(expo) / (np.power(a, 0.25) * np.power(U, 1.25))

def bsfg_log_density(e, a, delta):
    e = np.asarray(e, dtype=float)
    U = np.maximum(e - float(delta), EPS_U)
    return (0.5 * np.log(np.pi) - np.log(12.0)
            - 0.25 * np.log(np.maximum(a, 1e-12))
            - 1.25 * np.log(U)
            + 2.0 * np.sqrt(np.maximum(a, 1e-12) * U))

def fit_bsfg_log_weighted(e, y, sigma_log, cutoff):
    e = np.asarray(e, float)
    y = np.asarray(y, float)
    s = np.asarray(sigma_log, float)
    if np.any(s <= 0) or len(e) < 2:
        return None

    emin = float(np.min(e))
    delta_upper = min(float(cutoff), emin) - EPS_U  # enforce delta < cutoff
    a0 = 10.0
    delta0 = min(0.0, delta_upper - 0.1)           # safe initial guess below upper bound
    bounds = ([1e-4, -np.inf], [1e3, delta_upper])

    def f_log(e_, a, dlt):
        return bsfg_log_density(e_, a, dlt)

    try:
        popt, pcov = curve_fit(
            f_log, e, y, p0=[a0, delta0],
            sigma=s, absolute_sigma=True,
            bounds=bounds, maxfev=20000
        )
        a_fit, d_fit = popt
        if pcov is None or not np.all(np.isfinite(pcov)):
            da, dd = np.nan, np.nan
        else:
            errs = np.sqrt(np.diag(pcov))
            da, dd = float(errs[0]), float(errs[1])
    except Exception:
        return None

    return dict(a=a_fit, da=da, delta=d_fit, ddelta=dd)

# CT baseline
def fit_ct_high(e_high, y_high, var_high):
    e_high = np.asarray(e_high, float)
    y_high = np.asarray(y_high, float)
    var_high = np.maximum(np.asarray(var_high, float), MIN_VAR)
    if len(e_high) < 2:
        return None

    w = 1.0 / var_high
    if len(e_high) >= 3:
        try:
            (m0, b0), cov = np.polyfit(e_high, y_high, deg=1, w=w, cov=True)
            dm0, db0 = np.sqrt(np.diag(cov))
        except Exception:
            # fallback WLS
            A = np.vstack([e_high, np.ones(len(e_high))]).T
            W = np.sqrt(w)
            theta, *_ = np.linalg.lstsq(W[:, None]*A, W*y_high, rcond=None)
            m0, b0 = theta
            dm0, db0 = np.nan, np.nan
    else:
        m0, b0 = np.polyfit(e_high, y_high, deg=1, w=w)
        dm0, db0 = np.nan, np.nan

    resid = y_high - (m0*e_high + b0)
    chi2 = np.sum(resid**2 / var_high)
    dof = len(e_high) - 2
    chi2_dof = chi2 / dof if dof > 0 else np.nan
    return dict(m=m0, b=b0, dm=dm0, db=db0,
                chi2=chi2, dof=dof, chi2_dof=chi2_dof)


def load_cutoff_map(csv_path, cutoff_col):
    if not os.path.isfile(csv_path):
        print(f"error cannot find {csv_path}")
        sys.exit(1)
    scheme = pd.read_csv(csv_path)
    scheme["uc"] = scheme.iloc[:, cutoff_col]
    return {(int(row.Z), int(row.A)): float(row.uc) for _, row in scheme.iterrows()}

def read_nld_csv(path):
    """Return cleaned df with columns e, nld, sigma_nld, y, var_y, sigma_y; or None."""
    fname = os.path.basename(path)
    try:
        df = pd.read_csv(path, comment="#", header=None, names=["e", "nld", "sigma_nld"])
    except Exception:
        print(f"{fname}: (skip) failed to read")
        return None

    df = df.apply(pd.to_numeric, errors="coerce")
    if "sigma_nld" not in df:
        df["sigma_nld"] = np.nan

    # repair sigmas (assume 20% where missing or nonpositive)
    mask_bad = df["sigma_nld"].isna() | (df["sigma_nld"] <= 0)
    if mask_bad.any():
        print(f"{fname}: (warn) missing/zero sigma_nld assume 20percent")
        df.loc[mask_bad, "sigma_nld"] = 0.2 * df.loc[mask_bad, "nld"]

    df.dropna(subset=["e", "nld", "sigma_nld"], inplace=True)
    df = df[(df["e"] > 0) & (df["nld"] > 0)].copy()
    if len(df) < 4:
        print(f"{fname}: (skip) only {len(df)} valid points")
        return None

    df.sort_values("e", inplace=True)
    df.reset_index(drop=True, inplace=True)
    df["y"] = np.log(df["nld"])
    df["var_y"] = np.maximum((df["sigma_nld"] / df["nld"])**2, MIN_VAR)
    df["sigma_y"] = np.sqrt(df["var_y"])
    return df




def process_file_both(path, cutoff):
    fname = os.path.basename(path)
    base = os.path.splitext(fname)[0]
    out_png = os.path.join(fig_dir, f"{base}_composite.png")

    df = read_nld_csv(path)
    if df is None:
        return

    # split at cutoff 
    above = df["e"] > cutoff
    split_index = above.idxmax() if above.any() else len(df)
    end_low_index = min(split_index + 2, len(df) - 1)
    low = df.iloc[:end_low_index + 1].reset_index(drop=True)
    high = df.iloc[end_low_index + 1:].reset_index(drop=True)

    # Prepare plot
    e = df["e"].values
    rho = df["nld"].values
    sigma = df["sigma_nld"].values
    e_grid = np.linspace(e.min(), e.max(), 400)
    fig, ax = plt.subplots(figsize=(9.0, 5.6))
    ax.errorbar(e, rho, yerr=sigma, fmt="o", ms=3, lw=1, capsize=2, label="data")
    ax.set_yscale("log")
    ax.set_xlabel("E (MeV)")
    ax.set_ylabel("ρ(E) (MeV$^{-1}$)")

    # CT model (baseline + GP band)
    ct_ok = False
    mb_ct = False
    chi_ct_fail = False
    m0 = b0 = dm0 = db0 = mg = bg = dmg = dbg = np.nan
    chi2_ct = np.nan
    p_ct = np.nan
    if len(high) >= 2:
        ct = fit_ct_high(high["e"].values, high["y"].values, high["var_y"].values)
        if ct is not None:
            ct_ok = True
            m0, b0, dm0, db0, chi2_ct = ct["m"], ct["b"], ct["dm"], ct["db"], ct["chi2_dof"]
            chi2_ct_raw, dof_ct = ct["chi2"], ct["dof"]
            # survival function: p = P(chi2 >= observed | model correct)
            p_ct = float(chi2_dist.sf(chi2_ct_raw, dof_ct)) if dof_ct > 0 else np.nan

            # GP on low-E residuals
            low_ct = low.copy()
            low_ct["r"] = low_ct["y"] - (m0 * low_ct["e"] + b0)
            e_low = low_ct["e"].values.reshape(-1, 1)
            r_low = low_ct["r"].values
            var_low = low_ct["var_y"].values

            boundary_e = np.array([[cutoff]])
            boundary_r = np.array([0.0])
            boundary_var = np.array([var_low.min() * 1e-3 if len(var_low) else 1e-6])

            e_aug = np.vstack([e_low, boundary_e])
            r_aug = np.concatenate([r_low, boundary_r])
            var_aug = np.concatenate([var_low, boundary_var])

            gp_ct = GaussianProcessRegressor(
                kernel=gpr_kernel,
                alpha=var_aug,
                normalize_y=gpr_normalize_y,
                n_restarts_optimizer=gpr_restarts,
                random_state=0
            )
            gp_ct.fit(e_aug, r_aug)

            # Sample residuals to propagate to (m,b)
            m_samp = np.zeros(k_samples)
            b_samp = np.zeros(k_samples)
            e_high = high["e"].values
            y_high = high["y"].values
            w_high = 1.0 / high["var_y"].values
            e_low_1d = low_ct["e"].values
            w_low = 1.0 / low_ct["var_y"].values

            samples_ct = gp_ct.sample_y(e_aug, n_samples=k_samples, random_state=0)
            sampled_low_ct = samples_ct[:len(r_low), :]

            for i in range(k_samples):
                r_adj = sampled_low_ct[:, i]
                y_low_adj = low_ct["y"].values - r_adj
                A = np.vstack([
                    np.hstack([e_high.reshape(-1, 1), np.ones((len(e_high), 1))]),
                    np.hstack([e_low_1d.reshape(-1, 1), np.ones((len(e_low_1d), 1))])
                ])
                y_all = np.concatenate([y_high, y_low_adj])
                w_all = np.concatenate([w_high, w_low])
                W = np.sqrt(w_all)
                theta, *_ = np.linalg.lstsq(W[:, None] * A, W * y_all, rcond=None)
                m_samp[i], b_samp[i] = theta

            mg, bg = m_samp.mean(), b_samp.mean()
            dmg, dbg = m_samp.std(ddof=1), b_samp.std(ddof=1)
            mb_ct = not (within_two_sigma(m0, dm0, mg, dmg) and within_two_sigma(b0, db0, bg, dbg))
            chi_ct_fail = np.isfinite(p_ct) and (p_ct < P_VALUE_THRESHOLD)

            # Baseline curve
            y_ct_base_grid = m0 * e_grid + b0
            ax.plot(e_grid, np.exp(y_ct_base_grid), lw=1.8, label="CT baseline")

            # GP mean and ±1σ band on low side
            mask_low = e_grid <= cutoff
            if np.any(mask_low):
                mu_ct, std_ct = gp_ct.predict(e_grid[mask_low].reshape(-1, 1), return_std=True)
                y_ct_gp_mean = y_ct_base_grid[mask_low] + mu_ct
                ax.plot(e_grid[mask_low], np.exp(y_ct_gp_mean), lw=1.5, linestyle="--", label="CT + GP mean (low)")
                upper = np.exp(y_ct_gp_mean + std_ct)
                lower = np.exp(y_ct_gp_mean - std_ct)
                ax.fill_between(e_grid[mask_low], lower, upper, alpha=0.20, linewidth=0, label="CT GP ±1σ")

    # 2) BSFG (baseline + GP band, with Δ upper-bounded to cutoff)
    bsfg_ok = False
    mb_b = False
    chi_b_fail = False
    a0 = da0 = d0 = dd0 = ag = dag = dg = ddg = np.nan
    chi2_b_dof = np.nan
    p_b = np.nan
    if len(high) >= 2:
        # Baseline high-E fit with cutoff-bound delta
        fit_high = fit_bsfg_log_weighted(high["e"].values, high["y"].values, high["sigma_y"].values, cutoff)
        if (fit_high is not None
            and np.isfinite(fit_high["a"])
            and np.isfinite(fit_high["delta"])):
            bsfg_ok = True
            a0, da0 = fit_high["a"], fit_high["da"]
            d0, dd0 = fit_high["delta"], fit_high["ddelta"]

            y_high_model = bsfg_log_density(high["e"].values, a0, d0)
            resid_b = high["y"].values - y_high_model
            chi2_b = np.sum(resid_b**2 / np.maximum(high["var_y"].values, MIN_VAR))
            dof_b = len(high) - 2
            chi2_b_dof = chi2_b / dof_b if dof_b > 0 else np.nan
            p_b = float(chi2_dist.sf(chi2_b, dof_b)) if dof_b > 0 else np.nan
            chi_b_fail = np.isfinite(p_b) and (p_b < P_VALUE_THRESHOLD)

            # GP on low-E residuals; only E >= Delta
            low_b = low.copy()
            low_b["r"] = low_b["y"] - bsfg_log_density(low_b["e"].values, a0, d0)
            low_gp = low_b[low_b["e"] >= d0].reset_index(drop=True)

            if len(low_gp) == 0:
                ag, dag = a0, 0.0
                dg, ddg = d0, 0.0
                mb_b = False
                gp_b = None
            else:
                e_low_b = low_gp["e"].values.reshape(-1, 1)
                r_low_b = low_gp["r"].values
                var_low_b = np.maximum(low_gp["var_y"].values, MIN_VAR)

                boundary_E = float(max(cutoff, d0))
                boundary_e_b = np.array([[boundary_E]])
                boundary_r_b = np.array([0.0])
                boundary_var_b = np.array([var_low_b.min() * 1e-3 if len(var_low_b) else 1e-6])

                e_aug_b = np.vstack([e_low_b, boundary_e_b])
                r_aug_b = np.concatenate([r_low_b, boundary_r_b])
                var_aug_b = np.concatenate([var_low_b, boundary_var_b])

                gp_b = GaussianProcessRegressor(
                    kernel=gpr_kernel,
                    alpha=var_aug_b,
                    normalize_y=gpr_normalize_y,
                    n_restarts_optimizer=gpr_restarts,
                    random_state=0
                )
                gp_b.fit(e_aug_b, r_aug_b)

                a_samples = np.zeros(k_samples)
                d_samples = np.zeros(k_samples)

                samples_b = gp_b.sample_y(e_aug_b, n_samples=k_samples, random_state=0)
                sampled_low_b = samples_b[:len(r_low_b), :]

                e_high_b = high["e"].values
                y_high_b = high["y"].values
                s_high_b = high["sigma_y"].values

                e_low_b_1d = low_gp["e"].values
                s_low_b = low_gp["sigma_y"].values

                for i in range(k_samples):
                    r_adj = sampled_low_b[:, i]
                    y_low_adj = low_gp["y"].values - r_adj

                    e_all = np.concatenate([e_high_b, e_low_b_1d])
                    y_all = np.concatenate([y_high_b, y_low_adj])
                    s_all = np.concatenate([s_high_b, s_low_b])

                    # Refit with cutoff-bound delta on each draw
                    fit_all = fit_bsfg_log_weighted(e_all, y_all, s_all, cutoff)
                    if fit_all is None:
                        a_samples[i] = np.nan
                        d_samples[i] = np.nan
                    else:
                        a_samples[i] = fit_all["a"]
                        d_samples[i] = fit_all["delta"]

                a_s = a_samples[np.isfinite(a_samples)]
                d_s = d_samples[np.isfinite(d_samples)]
                ag = np.nan if len(a_s) == 0 else float(np.mean(a_s))
                dag = np.nan if len(a_s) == 0 else float(np.std(a_s, ddof=1) if len(a_s) > 1 else 0.0)
                dg = np.nan if len(d_s) == 0 else float(np.mean(d_s))
                ddg = np.nan if len(d_s) == 0 else float(np.std(d_s, ddof=1) if len(d_s) > 1 else 0.0)

                mb_b = not (within_two_sigma(a0, da0, ag, dag) and within_two_sigma(d0, dd0, dg, ddg))

            # Baseline BSFG curve
            y_bsfg_base_grid = bsfg_log_density(e_grid, a0, d0)
            ax.plot(e_grid, np.exp(y_bsfg_base_grid), lw=1.8, label="BSFG baseline")

            # GP mean & ±1σ band for BSFG on low side, restricted to E >= Delta
            if 'gp_b' in locals() and (gp_b is not None):
                mask_b = (e_grid >= d0) & (e_grid <= max(cutoff, d0))
                if np.any(mask_b):
                    mu_b, std_b = gp_b.predict(e_grid[mask_b].reshape(-1, 1), return_std=True)
                    y_b_gp_mean = y_bsfg_base_grid[mask_b] + mu_b
                    ax.plot(e_grid[mask_b], np.exp(y_b_gp_mean), lw=1.5, linestyle=":", label="BSFG + GP mean (low)")
                    upper_b = np.exp(y_b_gp_mean + std_b)
                    lower_b = np.exp(y_b_gp_mean - std_b)
                    ax.fill_between(e_grid[mask_b], lower_b, upper_b, alpha=0.20, linewidth=0, label="BSFG GP ±1σ")

    # Titles/legend and save
    title_bits = [fname]
    if ct_ok:
        title_bits.append(f"CT: m={m0:.4g}±{(dm0 if np.isfinite(dm0) else float('nan')):.2g}, "
                          f"b={b0:.4g}±{(db0 if np.isfinite(db0) else float('nan')):.2g}")
    if bsfg_ok:
        title_bits.append(f"BSFG: a={a0:.4g}±{(da0 if np.isfinite(da0) else float('nan')):.2g}, "
                          f"Δ={d0:.4g}±{(dd0 if np.isfinite(dd0) else float('nan')):.2g}")
    ax.set_title(" | ".join(title_bits))
    ax.legend(loc="best")
    ax.grid(True, which="both", linestyle="--", alpha=0.35)
    ax.axvline(float(cutoff), linestyle="--", linewidth=1.2, alpha=0.8, label=f"cutoff = {cutoff:.3g} MeV")
    plt.tight_layout()
    y_last = float(rho[-1])
    ax.set_ylim(top = 3.0 * y_last)
    # plt.savefig(out_png, dpi=200, bbox_inches="tight")
    print(f"saved figure -> {out_png}")

    # Terminal summaries
    if ct_ok:
        markers_ct = []
        if mb_ct: markers_ct.append("mb")
        if chi_ct_fail: markers_ct.append("chi")
        flag_ct = f" <- {','.join(markers_ct)} flag" if markers_ct else ""
        print(
            f"{fname} | CT: flat m={nice_pm(m0, dm0)} b={nice_pm(b0, db0)}  "
            f"gp m={nice_pm(mg, dmg)} b={nice_pm(bg, dbg)}  "
            f"cutoff={cutoff} chi2/dof={chi2_ct:.2f} p={p_ct:.3g}{flag_ct}"
        )
    else:
        print(f"{fname} | CT: (skip) failed or insufficient high-E points")

    if bsfg_ok:
        markers_b = []
        if mb_b: markers_b.append("mb")
        if chi_b_fail: markers_b.append("chi")
        flag_b = f" <- {','.join(markers_b)} flag" if markers_b else ""
        print(
            f"{fname} | BSFG: flat a={nice_pm(a0, da0)} Delta={nice_pm(d0, dd0)}  "
            f"gp a={nice_pm(ag, dag)} Delta={nice_pm(dg, ddg)}  "
            f"cutoff={cutoff} chi2/dof={chi2_b_dof:.2f} p={p_b:.3g}{flag_b}"
        )
    else:
        print(f"{fname} | BSFG: (skip) fit failed on high region")

    return dict(
        file=fname,
        m=m0, dm=dm0, b=b0, db=db0, chi2_ct=chi2_ct, p_ct=p_ct,
        mg=mg, dmg=dmg, bg=bg, dbg=dbg,
    ) if ct_ok else None


if __name__ == "__main__":
    cutoff_map = load_cutoff_map(scheme_csv, cutoff_col_index)
    files = sorted(glob.glob(os.path.join(data_dir, "NLD_*_*.csv")))
    print(f"found {len(files)} files in {data_dir}\n")

    ct_records = []
    for path in files:
        base = os.path.basename(path)[:-4]
        parts = base.split("_")
        try:
            z, a_mass = map(int, parts[1:3])
        except ValueError:
            print(f"{os.path.basename(path)}: (skip) bad filename format")
            continue
        cutoff = cutoff_map.get((z, a_mass))
        if cutoff is None:
            print(f"{os.path.basename(path)}: (skip) no cutoff for z={z} a={a_mass}")
            continue
        result = process_file_both(path, cutoff)
        if result is not None:
            ct_records.append({"Z": z, "A": a_mass, **result})

    # if ct_records:
    #     ct_csv = os.path.join(params_dir, "ct_parameters.csv")
    #     pd.DataFrame(ct_records).to_csv(ct_csv, index=False)
    #     print(f"\nSaved CT parameters -> {ct_csv}")

    print("\nDone.")
