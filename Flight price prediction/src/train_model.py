"""Train and save the notebook's flight-price regression model."""

import logging
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import ElasticNet, Lasso, LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, KFold, train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor


PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent
DATASET_PATH = Path(
    os.environ.get(
        "FLIGHT_PRICE_DATASET_PATH",
        PROJECT_DIRECTORY.parent / "DATA" / "flights.csv",
    )
)
MODEL_PATH = PROJECT_DIRECTORY / "artifacts" / "best_flight_price_model.joblib"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def check_dataset(dataset_path: str | Path = DATASET_PATH) -> str:
    """Fail early if the configured flight dataset is unavailable."""
    path = Path(dataset_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Flight dataset not found: {path}")
    logger.info("Dataset exists: %s", path)
    return str(path)


def train_model(
    dataset_path: str | Path = DATASET_PATH,
    model_path: str | Path = MODEL_PATH,
) -> str:
    """Run the notebook's preprocessing, evaluation, tuning, and save steps."""
    dataset_path = Path(dataset_path).expanduser().resolve()
    model_path = Path(model_path).expanduser().resolve()

    logger.info("Loading dataset from %s", dataset_path)
    flights = pd.read_csv(dataset_path)
    logger.info("Dataset loaded with shape %s", flights.shape)

    flights["date"] = pd.to_datetime(flights["date"])
    flights["month"] = flights["date"].dt.month
    flights["day"] = flights["date"].dt.day
    flights["day_of_week"] = flights["date"].dt.dayofweek
    flights["is_weekend"] = (flights["day_of_week"] >= 5).astype(int)
    flights.rename(columns={"to": "destination"}, inplace=True)
    flights = pd.get_dummies(
        flights,
        columns=["from", "destination", "flightType", "agency"],
        drop_first=False,
    )

    X = flights.drop(columns=["travelCode", "userCode", "date", "price"])
    y = flights["price"]
    logger.info("Preprocessing completed; feature matrix shape is %s", X.shape)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    logger.info(
        "Train/test split completed: train=%s, test=%s",
        X_train.shape,
        X_test.shape,
    )

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    models = {
        "Linear Regression": LinearRegression(),
        "Ridge Regression": Ridge(),
        "Lasso Regression": Lasso(),
        "ElasticNet Regression": ElasticNet(),
        "Decision Tree Regressor": DecisionTreeRegressor(),
        "Random Forest Regressor": RandomForestRegressor(),
        "Gradient Boosting Regressor": GradientBoostingRegressor(),
    }

    logger.info("Training and evaluating baseline models")
    results = []
    for name, model in models.items():
        logger.info("Training baseline model: %s", name)
        model.fit(X_train, y_train)
        prediction = model.predict(X_test)
        mse = mean_squared_error(y_test, prediction)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test, prediction)
        r2 = r2_score(y_test, prediction)
        results.append(
            {"Model": name, "MSE": mse, "RMSE": rmse, "MAE": mae, "R2 Score": r2}
        )
        logger.info(
            "%s results: MSE=%.4f RMSE=%.4f MAE=%.4f R2=%.4f",
            name,
            mse,
            rmse,
            mae,
            r2,
        )
    results_df = pd.DataFrame(results)
    logger.info("Baseline model comparison:\n%s", results_df.to_string(index=False))

    logger.info("Starting 5-fold shuffled cross-validation for Linear Regression")
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    lr = LinearRegression()
    fold_results = []

    for fold, (train_index, test_index) in enumerate(kf.split(X), 1):
        X_train_fold = X.iloc[train_index]
        X_test_fold = X.iloc[test_index]
        y_train_fold = y.iloc[train_index]
        y_test_fold = y.iloc[test_index]

        X_train_fold = scaler.fit_transform(X_train_fold)
        X_test_fold = scaler.transform(X_test_fold)

        lr.fit(X_train_fold, y_train_fold)
        prediction = lr.predict(X_test_fold)
        fold_results.append(
            {
                "Fold": fold,
                "MSE": round(mean_squared_error(y_test_fold, prediction), 4),
                "RMSE": round(np.sqrt(mean_squared_error(y_test_fold, prediction)), 4),
                "MAE": round(mean_absolute_error(y_test_fold, prediction), 4),
                "R2": round(r2_score(y_test_fold, prediction), 4),
            }
        )
        logger.info("Linear Regression cross-validation fold %s completed", fold)

    cv_df = pd.DataFrame(fold_results)
    logger.info("Cross-validation fold results:\n%s", cv_df.to_string(index=False))
    logger.info(
        "Cross-validation average scores:\n%s",
        cv_df[["MSE", "RMSE", "MAE", "R2"]].mean().to_string(),
    )

    tuning_configs = {
        "Ridge": (Ridge(), {"alpha": [0.1, 1.0, 10.0]}),
        "Lasso": (Lasso(max_iter=10000), {"alpha": [0.01, 0.1, 1.0]}),
        "DecisionTree": (
            DecisionTreeRegressor(random_state=42),
            {"max_depth": [5, 10], "min_samples_split": [2, 5]},
        ),
        "RandomForest": (
            RandomForestRegressor(random_state=42),
            {"n_estimators": [50, 100], "max_depth": [5, 10]},
        ),
        "GradientBoosting": (
            GradientBoostingRegressor(random_state=42),
            {"n_estimators": [50, 100], "learning_rate": [0.1, 0.2]},
        ),
    }

    tuning_results = []
    best_models = {}
    for name, (model, param_grid) in tuning_configs.items():
        logger.info("Starting GridSearchCV for %s with parameters %s", name, param_grid)
        grid = GridSearchCV(model, param_grid, cv=5, scoring="r2", n_jobs=-1)
        grid.fit(X_train, y_train)

        best_model = grid.best_estimator_
        prediction = best_model.predict(X_test)
        best_models[name] = best_model
        tuning_results.append(
            {
                "Model": name,
                "Best_Params": str(grid.best_params_),
                "CV_R2_Mean": round(grid.best_score_, 4),
                "MSE_Test": round(mean_squared_error(y_test, prediction), 4),
                "RMSE_Test": round(np.sqrt(mean_squared_error(y_test, prediction)), 4),
                "MAE_Test": round(mean_absolute_error(y_test, prediction), 4),
                "R2_Test": round(r2_score(y_test, prediction), 4),
            }
        )
        logger.info(
            "GridSearchCV completed for %s: best_params=%s, CV_R2=%.4f",
            name,
            grid.best_params_,
            grid.best_score_,
        )

    tuning_df = pd.DataFrame(tuning_results)
    logger.info("Tuned model comparison:\n%s", tuning_df.to_string(index=False))

    best_rf_model = best_models["RandomForest"]
    random_forest_result = tuning_df[tuning_df["Model"] == "RandomForest"].iloc[0]
    logger.info("Selected best model: %s", best_rf_model)
    logger.info("Selected model parameters: %s", best_rf_model.get_params())
    logger.info("Selected model test R2 score: %s", random_forest_result["R2_Test"])

    model_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Saving the best model to %s", model_path)
    joblib.dump(best_rf_model, model_path)

    logger.info("Loading the saved model for the notebook's sanity check")
    loaded_model = joblib.load(model_path)
    unseen_predictions = loaded_model.predict(X_test[:10])
    sanity_check = pd.DataFrame(
        {
            "Actual Price": y_test[:10].values,
            "Predicted Price": unseen_predictions.round(2),
            "Difference": (y_test[:10].values - unseen_predictions).round(2),
        }
    )
    logger.info("Sanity check results:\n%s", sanity_check.to_string(index=False))
    avg_error = abs(sanity_check["Difference"]).mean()
    logger.info("Average absolute error on unseen data: %.2f", avg_error)
    logger.info("Model saved and verified successfully at %s", model_path)
    return str(model_path)


if __name__ == "__main__":
    train_model()