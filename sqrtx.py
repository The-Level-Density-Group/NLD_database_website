import numpy as np
import matplotlib.pyplot as plt
from pysr import PySRRegressor
from sklearn.model_selection import train_test_split

N_POINTS = 200
NOISE_SIGMA = 0.4
X_MIN = 0.0
X_MAX = 10.0
TEST_SIZE = 0.80
RANDOM_STATE = 0

NITERATIONS = 300
MAXSIZE = 24

def true_function(x):
    return np.sqrt(x) + 2.0 * x

def rmse(a, b):
    a = np.asarray(a)
    b = np.asarray(b)
    return float(np.sqrt(np.mean((a - b) ** 2)))

def main():
    rng = np.random.default_rng(RANDOM_STATE)
    x = np.linspace(X_MIN, X_MAX, N_POINTS)
    y_true = true_function(x)
    y = y_true + rng.normal(0.0, NOISE_SIGMA, size=N_POINTS)

    X = x.reshape(-1, 1)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )

    model = PySRRegressor(
        niterations=NITERATIONS,
        maxsize=MAXSIZE,
        binary_operators=["+", "-", "*", "/"],
        unary_operators=["sqrt"],
        model_selection="best",
        random_state=RANDOM_STATE,
        verbosity=1,
    )

    model.fit(X_train, y_train)

    yhat_test = model.predict(X_test)
    test_rmse = rmse(yhat_test, y_test)

    x_grid = np.linspace(X_MIN, X_MAX, 600)
    y_pred = model.predict(x_grid.reshape(-1, 1))

    plt.figure(figsize=(8, 5))
    plt.scatter(x, y, s=18, label="Noisy data")
    plt.plot(x, y_true, linewidth=2, label="True: sqrt(x) + 2x")
    plt.plot(x_grid, y_pred, linewidth=2, label="PySR fit")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.title("PySR recovering y = sqrt(x) + 2x from noisy samples")
    plt.legend()
    plt.show()

    print("\nSelected equation:")
    print(model)
    print(f"\nTest RMSE: {test_rmse:.6g}")


if __name__ == "__main__":
    main()
