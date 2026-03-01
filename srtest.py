import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pysr import PySRRegressor
from sklearn.model_selection import train_test_split

NLD_FILE = "data/NLD_32_70_1.csv"
COL_E = "E"
COL_RHO = "rho"

TEST_SIZE = 0.20
RANDOM_STATE = 0
MIN_RHO = 1e-300

NITERATIONS = 400
MAXSIZE = 18
BINARY_OPS = ["+", "-", "*"]
UNARY_OPS = ["exp", "log", "sqrt"]

def rmse(a, b):
    a = np.asarray(a)
    b = np.asarray(b)
    return float(np.sqrt(np.mean((a - b) ** 2)))

def load_table(path):
    df = pd.read_csv(path, sep=None, engine="python", comment="#")
    if df.shape[1] >= 2 and (COL_E not in df.columns or COL_RHO not in df.columns):
        if df.columns.to_list() == list(range(df.shape[1])):
            df = df.copy()
            df.columns = [COL_E, COL_RHO] + [f"col{i}" for i in range(2, df.shape[1])]
    return df

def infer_columns(df):
    if COL_E in df.columns and COL_RHO in df.columns:
        return COL_E, COL_RHO
    numeric = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if len(numeric) < 2:
        raise ValueError("Could not find two numeric columns for E and rho.")
    return numeric[0], numeric[1]

def clean_and_build_xy(df, e_col, rho_col):
    E = df[e_col].to_numpy(dtype=float)
    rho = df[rho_col].to_numpy(dtype=float)
    rho = np.clip(rho, MIN_RHO, None)
    mask = np.isfinite(E) & np.isfinite(rho) & (rho > 0)
    E = E[mask]
    rho = rho[mask]
    X = E.reshape(-1, 1)
    y = np.log(rho)
    return X, y, E, rho

def main():
    df = load_table(NLD_FILE)
    e_col, rho_col = infer_columns(df)
    X, y, E, rho = clean_and_build_xy(df, e_col, rho_col)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )

    model = PySRRegressor(
        niterations=NITERATIONS,
        maxsize=MAXSIZE,
        binary_operators=BINARY_OPS,
        unary_operators=UNARY_OPS,
        model_selection="best",
        random_state=RANDOM_STATE,
        verbosity=1,
    )

    model.fit(X_train, y_train)

    yhat_test = model.predict(X_test)
    test_rmse = rmse(yhat_test, y_test)

    eqs = model.equations_.sort_values("score", ascending=False)
    eqs.to_csv("sr_equations_NLD_32_70_1.csv", index=False)

    E_grid = np.linspace(E.min(), E.max(), 500).reshape(-1, 1)
    logrho_pred = model.predict(E_grid)
    rho_pred = np.exp(logrho_pred)

    out = pd.DataFrame(
        {
            "E": E_grid.ravel(),
            "rho_pred": rho_pred,
            "logrho_pred": logrho_pred,
        }
    )
    out.to_csv("sr_predictions_NLD_32_70_1.csv", index=False)

    plt.figure(figsize=(8, 5))
    plt.scatter(E, np.log(rho), s=16, label="Data: log(rho)")
    plt.plot(E_grid.ravel(), logrho_pred, linewidth=2, label="PySR fit (log-space)")
    plt.xlabel("E")
    plt.ylabel("log(rho)")
    plt.title("PySR fit for NLD_32_70_1.csv")
    plt.legend()
    plt.show()

    print(model)
    print(f"\nTest RMSE (log-space): {test_rmse:.6g}")

if __name__ == "__main__":
    main()
