#!/usr/bin/env python3

#########################################
"visualization of GP for a selected file."
##########################################
import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.linear_model import LinearRegression
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, RBF

Z = 92           
A = 239          
E_CUTOFF = 1.635

DEFAULT_CSV = os.path.join(
    "data",
    "Nuclear Level Densities",
    "NLD_92_239_1.csv"
)

def main(csv_path):
    df = pd.read_csv(csv_path, header=None, names=['E','NLD','sigma_NLD'])
    df['y']     = np.log(df['NLD'])
    df['y_err'] = df['sigma_NLD'] / df['NLD']
    df['var_y'] = df['y_err']**2

    # split at the fixed cutoff energy
    high = df[df['E'] > E_CUTOFF].copy().reset_index(drop=True)
    low  = df[df['E'] <= E_CUTOFF].copy().reset_index(drop=True)

    # weighted linear fit on the high-energy block
    lin = LinearRegression()
    w_high = 1.0 / high['var_y'].values
    lin.fit(high[['E']], high['y'], sample_weight=w_high)
    a, b = lin.coef_[0], lin.intercept_

    # store linear predictions
    high['y_lin'] = lin.predict(high[['E']])

    # residuals on the low-energy block
    low['y_lin'] = lin.predict(low[['E']])
    low['r']     = low['y'] - low['y_lin']

    # alternating train/test split for low-energy block
    mask_train = (np.arange(len(low)) % 2 == 0)
    mask_test  = ~mask_train

    E_train = low.loc[mask_train, ['E']].values
    r_train = low.loc[mask_train, 'r'].values
    var_train = low.loc[mask_train, 'var_y'].values

    E_test  = low.loc[mask_test, ['E']].values
    r_test  = low.loc[mask_test, 'r'].values

    kernel = ConstantKernel(1.0, (1e-3,1e3)) * RBF(1.0, (1e-2,1e2))
    gp = GaussianProcessRegressor(
        kernel=kernel,
        alpha=var_train,        # per-point variance
        normalize_y=True,
        n_restarts_optimizer=10
    )
    gp.fit(E_train, r_train)

    # predictions
    E_full = np.linspace(df['E'].min(), df['E'].max(), 300).reshape(-1,1)
    y_lin_full = lin.predict(E_full)

    r_mean_full, r_std_full = gp.predict(E_full, return_std=True)
    y_pred_full = y_lin_full + r_mean_full
    # for E > cutoff, drop GP correction
    y_pred_full[E_full.ravel() > E_CUTOFF] = \
        y_lin_full[E_full.ravel() > E_CUTOFF]

    # high-energy + linear
    plt.figure(figsize=(8,6))
    plt.scatter(high['E'], high['y'], label='High-E data', alpha=0.7)
    plt.plot(E_full, y_lin_full, 'r--',
             label=f'Weighted linear fit (E > {E_CUTOFF:.5f})')
    plt.axvline(E_CUTOFF, color='gray', linestyle=':',
                label=f'Cutoff = {E_CUTOFF:.5f} MeV')
    plt.xlabel('Energy (MeV)')
    plt.ylabel('ln(NLD)')
    plt.title(f'Isotope Z={Z}, A={A} — High-Energy Block & Linear Trend')
    plt.legend()
    plt.tight_layout()
    plt.show()

    # low energy residuals + GP
    plt.figure(figsize=(8,6))
    plt.scatter(E_train, r_train, marker='o', label='Low-E train residuals')
    plt.scatter(E_test,  r_test,  marker='x', label='Low-E test residuals')
    mask_low_full = (E_full.ravel() <= E_CUTOFF)
    plt.plot(E_full[mask_low_full], r_mean_full[mask_low_full], 'k-',
             label='GP mean(residuals)')
    plt.fill_between(
        E_full[mask_low_full].ravel(),
        r_mean_full[mask_low_full] - r_std_full[mask_low_full],
        r_mean_full[mask_low_full] + r_std_full[mask_low_full],
        alpha=0.2, label='±1σ band'
    )
    plt.axvline(E_CUTOFF, color='gray', linestyle=':')
    plt.xlabel('Energy (MeV)')
    plt.ylabel('Residual = ln(NLD) – linear(E)')
    plt.title(f'Isotope Z={Z}, A={A} — Low-Energy Block: GP on Residuals')
    plt.legend()
    plt.tight_layout()
    plt.show()

    # combined model
    plt.figure(figsize=(8,6))
    plt.scatter(df['E'], df['y'], s=20, alpha=0.5, label='All data')
    plt.plot(E_full, y_pred_full, 'm-', label='Composite model')
    plt.axvline(E_CUTOFF, color='gray', linestyle=':')
    plt.xlabel('Energy (MeV)')
    plt.ylabel('ln(NLD)')
    plt.title(f'Isotope Z={Z}, A={A} — Composite Model')
    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__=="__main__":
    path = sys.argv[1] if len(sys.argv)==2 else DEFAULT_CSV
    if not os.path.isfile(path):
        print(f"File not found: {path}")
        sys.exit(1)
    main(path)
