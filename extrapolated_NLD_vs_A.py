import os
import re
import numpy as np
import matplotlib.pyplot as plt

DATA_FOLDER = "data/Nuclear Level Densities"
E_TARGET    = 6.0   # MeV
MAGIC_A = sorted({20, 58, 100, 164, 208, 4, 16, 40, 120, 48, 132, 78})
count = 0


def parse_filename(fname):
    """
    Match NLD_Z_A.csv or NLD_Z_A_i.csv → (Z, A), else (None, None).
    """
    m = re.match(r"^NLD_(\d+)_(\d+)(?:_\d+)?\.csv$", fname)
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2))

def read_nld_manual(path):
    # Read E, rho, uncertainty from a CSV.
    # If missing or invalid uncertainty -> assume 10% of rho (count these).
    # Skip rows with E < 0, rho ≤ 0, unc < 0, or non-finite.
    # Returns: (E_arr, rho_arr, unc_arr, assumed_count).
    # If fewer than 2 valid rows, returns ([],[],[], assumed_count).
    E_list, rho_list, unc_list = [], [], []
    assumed_count = 0
    flagged_count = 0

    with open(path, 'r') as f:
        for line in f:
            parts = line.strip().split(',')
            if len(parts) < 2:
                continue

            # 1) Parse E and rho
            try:
                Ev = float(parts[0])
                rv = float(parts[1])
            except ValueError:
                continue

            # 2) Determine uncertainty (dv)
            if len(parts) >= 3:
                # try converting third column
                try:
                    dv = float(parts[2])
                    if dv <= 0:
                        # treat non-positive as missing
                        raise ValueError
                except ValueError:
                    dv = 0.1 * rv
                    assumed_count += 1
            else:
                dv = 0.1 * rv
                assumed_count += 1

            # 3) Filter out invalid rows
            if Ev < 0 or rv <= 0 or dv < 0:
                continue
            if not (np.isfinite(rv) and np.isfinite(dv)):
                continue

            E_list.append(Ev)
            rho_list.append(rv)
            unc_list.append(dv)

    if len(E_list) < 2:
        return np.array([]), np.array([]), np.array([]), assumed_count

    E_arr = np.array(E_list)
    rho_arr = np.array(rho_list)
    unc_arr = np.array(unc_list)
    order = np.argsort(E_arr)
    return E_arr[order], rho_arr[order], unc_arr[order], assumed_count

# ——— MAIN LOOP ———
mass_list = []
nld6_list = []

for fname in sorted(os.listdir(DATA_FOLDER)):
    if not fname.lower().endswith(".csv"):
        continue

    Z, A = parse_filename(fname)
    if A is None:
        print(f"SKIP bad filename: {fname}")
        continue

    path = os.path.join(DATA_FOLDER, fname)
    E, rho, unc, assumed = read_nld_manual(path)

    # If we assumed any uncertainties, print a brief note
    if assumed > 0:
        print(f"NOTE {fname}: assumed 10% unc for {assumed} row(s).")

    N = len(E)
    if N < 2:
        print(f"SKIP {fname}: only {N} valid data point(s).")
        continue

    # fit ln(rho) = m·E + b
    ln_rho = np.log(rho)
    m, b = np.polyfit(E, ln_rho, 1)

    # Δlnρᵢ = Δρᵢ / ρᵢ
    delta_ln = unc / rho

    # compute χ² in ln-space
    resid = ln_rho - (m * E + b)
    chi2 = np.sum((resid / delta_ln) ** 2)

    # degrees of freedom and χ²/dof
    dof = N - 2
    chi2_dof = chi2 / dof if dof > 0 else np.nan
    # flag = "  <-- FLAG χ²/dof>5" if chi2_dof > 5 else ""
    if chi2_dof>3:
        flag = "  <-- FLAG χ²/dof>3"
        count = count + 1
    else:
        flag = ""

    # avg Δlnρ
    avg_dln = np.mean(delta_ln)

    # extrapolate to 6 MeV
    ln_rho6 = m * E_TARGET + b
    rho6 = np.exp(ln_rho6)

    print(
        f"OK {fname}: "
        f"N={N}, m={m:.3f}, b={b:.3f}, "
        f"χ²={chi2:.1f}, χ²/dof={chi2_dof:.2f}, "
        f"avgΔlnρ={avg_dln:.3f}, "
        f"lnρ(6)={ln_rho6:.3f}, ρ(6)={rho6:.3e}"
        f"{flag}"
    )

    mass_list.append(A)
    nld6_list.append(rho6)

# ——— PLOT ———
if mass_list:
    As = np.array(mass_list)
    R6 = np.array(nld6_list)
    order = np.argsort(As)
    As = As[order]
    R6 = R6[order]

    plt.figure(figsize=(8,5))
    plt.scatter(As, R6, marker='o', c='tab:blue', label='NLD(6 MeV)')

    for mag in MAGIC_A:
        plt.axvline(x=mag, color='red', linestyle='--', alpha=0.7)

    plt.yscale('log')
    plt.xlabel("Atomic Mass A")
    plt.ylabel(f"NLD at {E_TARGET:.1f} MeV (1/MeV)")
    plt.title("Extrapolated NLD(6 MeV) vs A")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()

    print(f"\nPlotted {len(R6)} points.")
    print (f"\nFlagged {count} points")
else:
    print("No valid data found.")

print (f"\nFlagged {count} points")

