# script to process nuclear level density csv files and flag datasets
# reads discrete level scheme csv for cutoff values
# applies baseline linear fit at high energies
# applies gaussian process residual sampling at low energies
# flags datasets based on mb mismatch or chi squared per dof
# prints summary counts


import os
import sys
import glob
import warnings

import numpy as np
import pandas as pd
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, RBF
from sklearn.exceptions import ConvergenceWarning

# suppress convergence warnings from gaussian process
warnings.filterwarnings("ignore", category=ConvergenceWarning)
# ignore invalid numerical operations at runtime
np.seterr(invalid="ignore", divide="ignore")

# path to data directory containing nuclear level density files
data_dir = os.path.join(".", "data", "Nuclear Level Densities")
# csv file listing discrete level schemes and cutoff values
scheme_csv = "Discrete_Level_Scheme.csv"
# zero based index of cutoff column in scheme_csv (uc)
cutoff_col_index = 11
# number of samples to draw from gaussian process for residual uncertainty
k_samples = 50


def within_two_sigma(m0, dm0, mg, dmg):
    """
    check if mg differs from m0 by less than two times combined standard error
    arguments:
      m0: baseline slope
      dm0: baseline slope error
      mg: mean slope from sampling
      dmg: sampled slope standard deviation
    returns:
      boolean indicating if difference is within two sigma
    """
    return abs(mg - m0) < 2 * np.sqrt((dm0 or 0) ** 2 + dmg ** 2)


# load discrete level scheme and build cutoff lookup map
if not os.path.isfile(scheme_csv):
    print(f"error cannot find {scheme_csv}")
    sys.exit(1)
scheme = pd.read_csv(scheme_csv)
# read cutoff column into new uc column
scheme['uc'] = scheme.iloc[:, cutoff_col_index]
# map of (z,a) tuple to cutoff value
cutoff_map = {(int(row.Z), int(row.A)): float(row.uc)
              for _, row in scheme.iterrows()}

# counters for summary
skip_count = 0
mb_flag_count = 0
chi_flag_count = 0


def process_file(path, cutoff):
    """
    process single csv file at given path using cutoff
    reads energy and nld columns
    applies baseline linear fit to high energy region
    applies gaussian process to residuals in low energy region
    prints result line and updates summary counters
    """
    global skip_count, mb_flag_count, chi_flag_count
    fname = os.path.basename(path)

    # read data columns and ensure numeric types
    df = pd.read_csv(path, comment="#", header=None,
                     names=["e", "nld", "sigma_nld"])
    df = df.apply(pd.to_numeric, errors="coerce")

    # warn if sigma_nld missing and assume 20 percent error
    if df['sigma_nld'].isna().any():
        print(f"{fname}: (warn) missing sigma_nld assume 20percent")
        df['sigma_nld'].fillna(0.2 * df['nld'], inplace=True)

    # drop invalid rows and require positive energy and nld
    df.dropna(subset=["e", "nld", "sigma_nld"], inplace=True)
    df = df[(df['e'] > 0) & (df['nld'] > 0)]
    if len(df) < 4:
        print(f"{fname}: (skip) only {len(df)} valid points")
        skip_count += 1
        return

    # sort by energy and compute log of nld and its variance
    df = df.sort_values('e').reset_index(drop=True)
    df['y'] = np.log(df['nld'])
    df['var_y'] = (df['sigma_nld'] / df['nld']) ** 2

    # split data at cutoff with two extra low energy points
    above = df['e'] > cutoff
    split_index = above.idxmax() if above.any() else len(df)
    end_low_index = min(split_index + 2, len(df) - 1)
    low = df.iloc[:end_low_index + 1].reset_index(drop=True)
    high = df.iloc[end_low_index + 1:].reset_index(drop=True)

    if len(high) < 2:
        print(f"{fname}: (skip) insufficient high points ({len(high)})")
        skip_count += 1
        return

    # weighted linear fit on high energy region
    weights_high = 1.0 / high['var_y'].values
    if len(high) >= 3:
        try:
            (m0, b0), cov = np.polyfit(
                high['e'], high['y'], deg=1,
                w=weights_high, cov=True
            )
            dm0, db0 = np.sqrt(np.diag(cov))
        except Exception:
            print(f"{fname}: (skip) failed polyfit cov")
            skip_count += 1
            return
    else:
        m0, b0 = np.polyfit(high['e'], high['y'], deg=1, w=weights_high)
        dm0, db0 = np.nan, np.nan

    # compute chi squared per degree of freedom for high region
    residuals = high['y'] - (m0 * high['e'] + b0)
    chi2 = np.sum(residuals ** 2 / high['var_y'])
    dof = len(high) - 2
    chi2_per_dof = chi2 / dof if dof > 0 else np.nan
    chi_fail = chi2_per_dof > 3
    if chi_fail:
        chi_flag_count += 1

    # prepare low energy residuals for gp
    low['r'] = low['y'] - (m0 * low['e'] + b0)
    e_low = low['e'].values.reshape(-1, 1)
    r_low = low['r'].values
    var_low = low['var_y'].values

    # enforce zero residual at boundary by synthetic point
    boundary_e = np.array([[cutoff]])
    boundary_r = np.array([0.0])
    boundary_var = np.array([var_low.min() * 1e-3 if len(var_low) else 1e-6])

    # combine low energy and boundary for gp fitting
    e_aug = np.vstack([e_low, boundary_e])
    r_aug = np.concatenate([r_low, boundary_r])
    var_aug = np.concatenate([var_low, boundary_var])

    # fit gaussian process to residuals
    gp = GaussianProcessRegressor(
        kernel=ConstantKernel(1.0, (1e-3, 1e3)) * RBF(1.0, (1e-2, 1e2)),
        alpha=var_aug, normalize_y=True, n_restarts_optimizer=5
    )
    gp.fit(e_aug, r_aug)

    # sample residuals for original low points
    samples = gp.sample_y(e_aug, n_samples=k_samples, random_state=0)
    sampled_low = samples[:len(r_low), :]

    # resample combined fits using sampled residuals
    m_samples = np.zeros(k_samples)
    b_samples = np.zeros(k_samples)
    e_high = high['e'].values.reshape(-1, 1)
    y_high = high['y'].values
    w_high = 1.0 / high['var_y'].values

    for i in range(k_samples):
        r_adj = sampled_low[:, i]
        y_low_adj = low['y'].values - r_adj
        A = np.vstack([
            np.hstack([e_high, np.ones((len(e_high), 1))]),
            np.hstack([e_low, np.ones((len(e_low), 1))])
        ])
        y_all = np.concatenate([y_high, y_low_adj])
        w_all = np.concatenate([w_high, 1.0 / low['var_y'].values])
        W = np.sqrt(w_all)
        theta, *_ = np.linalg.lstsq(W[:, None] * A, W * y_all, rcond=None)
        m_samples[i], b_samples[i] = theta

    # compute mean and std of sampled slopes and intercepts
    mg = m_samples.mean()
    bg = b_samples.mean()
    dmg = m_samples.std(ddof=1)
    dbg = b_samples.std(ddof=1)

    # check for mismatch in slope or intercept
    mb_fail = not (within_two_sigma(m0, dm0, mg, dmg) and
                   within_two_sigma(b0, db0, bg, dbg))
    if mb_fail:
        mb_flag_count += 1

    # assemble flags for output
    markers = []
    if mb_fail:
        markers.append('mb')
    if chi_fail:
        markers.append('chi')
    flag_str = f" <- {','.join(markers)} flag" if markers else ''

    print(
        f"{fname}: flat m={m0:.4f}±{dm0:.4f} b={b0:.4f}±{db0:.4f}  "
        f"gp m={mg:.4f}±{dmg:.4f} b={bg:.4f}±{dbg:.4f}  "
        f"cut off={cutoff} chi2/dof={chi2_per_dof:.2f}{flag_str}"
    )


if __name__ == '__main__':
    # gather all nld csv files
    files = sorted(glob.glob(os.path.join(data_dir, 'NLD_*_*.csv')))
    print(f"found {len(files)} files in {data_dir}\n")

    # process each file using its z,a values to lookup cutoff
    for path in files:
        base = os.path.basename(path)[:-4]
        parts = base.split('_')
        try:
            z, a = map(int, parts[1:3])
        except ValueError:
            print(f"{os.path.basename(path)}: (skip) bad filename format")
            skip_count += 1
            continue
        cutoff = cutoff_map.get((z, a))
        if cutoff is None:
            print(f"{os.path.basename(path)}: (skip) no cutoff for z={z} a={a}")
            skip_count += 1
            continue
        process_file(path, cutoff)

    # print summary of results
    print("\nsummary:")
    print(f"  skipped datasets {skip_count}")
    print(f"  flagged by mb mismatch {mb_flag_count}")
    print(f"  flagged by chi squared {chi_flag_count}")
