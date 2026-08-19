"""
Machine learning model training module for Financial Fraud Detection.
Implements Stratified K-Fold Cross Validation, hyperparameter tuning,
and class imbalance treatment across Logistic Regression, Random Forest, and XGBoost models.
"""

from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.model_selection import StratifiedKFold, RandomizedSearchCV, GridSearchCV
from sklearn.metrics import make_scorer, average_precision_score
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Primary Random State for Reproducibility
RANDOM_STATE = 42


def get_cv_strategy(n_splits: int = 5) -> StratifiedKFold:
    """Returns StratifiedKFold cross-validation iterator."""
    return StratifiedKFold(
        n_splits=n_splits,
        shuffle=True,
        random_state=RANDOM_STATE
    )


def train_logistic_regression(
    X_train: np.ndarray,
    y_train: pd.Series,
    cv: StratifiedKFold
) -> Tuple[Any, float]:
    """
    Train and tune Logistic Regression classifier with class weights.
    """
    logger.info("Training & tuning Logistic Regression Classifier...")
    base_model = LogisticRegression(
        class_weight="balanced",
        max_iter=1000,
        random_state=RANDOM_STATE
    )

    param_grid = {
        "C": [0.01, 0.1, 1.0, 10.0, 100.0],
        "solver": ["lbfgs", "liblinear"]
    }

    grid_search = GridSearchCV(
        estimator=base_model,
        param_grid=param_grid,
        cv=cv,
        scoring="average_precision",
        n_jobs=-1
    )

    grid_search.fit(X_train, y_train)
    best_model = grid_search.best_estimator_
    best_cv_pr_auc = grid_search.best_score_

    logger.info(f"Logistic Regression Best CV PR-AUC: {best_cv_pr_auc:.4f} with params: {grid_search.best_params_}")
    return best_model, best_cv_pr_auc


def train_random_forest(
    X_train: np.ndarray,
    y_train: pd.Series,
    cv: StratifiedKFold
) -> Tuple[Any, float]:
    """
    Train and tune Random Forest Classifier with balanced class weights.
    """
    logger.info("Training & tuning Random Forest Classifier...")
    base_model = RandomForestClassifier(
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1
    )

    param_distributions = {
        "n_estimators": [100, 200, 300],
        "max_depth": [5, 10, 15, None],
        "min_samples_split": [2, 5, 10],
        "min_samples_leaf": [1, 2, 4],
        "max_features": ["sqrt", "log2"]
    }

    random_search = RandomizedSearchCV(
        estimator=base_model,
        param_distributions=param_distributions,
        n_iter=10,
        cv=cv,
        scoring="average_precision",
        random_state=RANDOM_STATE,
        n_jobs=-1
    )

    random_search.fit(X_train, y_train)
    best_model = random_search.best_estimator_
    best_cv_pr_auc = random_search.best_score_

    logger.info(f"Random Forest Best CV PR-AUC: {best_cv_pr_auc:.4f} with params: {random_search.best_params_}")
    return best_model, best_cv_pr_auc


def train_xgboost(
    X_train: np.ndarray,
    y_train: pd.Series,
    cv: StratifiedKFold
) -> Tuple[Any, float]:
    """
    Train and tune XGBoost Classifier with scale_pos_weight for class imbalance.
    """
    logger.info("Training & tuning XGBoost Classifier...")
    # Calculate scale_pos_weight = negative_count / positive_count
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()
    scale_pos_weight = float(neg_count / max(pos_count, 1))

    base_model = XGBClassifier(
        scale_pos_weight=scale_pos_weight,
        random_state=RANDOM_STATE,
        eval_metric="logloss",
        n_jobs=-1
    )

    param_distributions = {
        "n_estimators": [100, 200, 300],
        "max_depth": [3, 5, 7],
        "learning_rate": [0.01, 0.05, 0.1, 0.2],
        "subsample": [0.7, 0.8, 1.0],
        "colsample_bytree": [0.7, 0.8, 1.0],
        "min_child_weight": [1, 3, 5]
    }

    random_search = RandomizedSearchCV(
        estimator=base_model,
        param_distributions=param_distributions,
        n_iter=10,
        cv=cv,
        scoring="average_precision",
        random_state=RANDOM_STATE,
        n_jobs=-1
    )

    random_search.fit(X_train, y_train)
    best_model = random_search.best_estimator_
    best_cv_pr_auc = random_search.best_score_

    logger.info(f"XGBoost Best CV PR-AUC: {best_cv_pr_auc:.4f} with params: {random_search.best_params_}")
    return best_model, best_cv_pr_auc


def train_all_models(
    X_train: np.ndarray,
    y_train: pd.Series
) -> Dict[str, Dict[str, Any]]:
    """
    Trains, tunes, and cross-validates Logistic Regression, Random Forest, and XGBoost models.

    Returns:
        Dict mapping model name to dict containing trained model instance and CV PR-AUC score.
    """
    logger.info("Starting model training pipeline across all candidates...")
    cv = get_cv_strategy(n_splits=5)

    lr_model, lr_cv_score = train_logistic_regression(X_train, y_train, cv)
    rf_model, rf_cv_score = train_random_forest(X_train, y_train, cv)
    xgb_model, xgb_cv_score = train_xgboost(X_train, y_train, cv)

    models_dict = {
        "Logistic Regression": {
            "model": lr_model,
            "cv_pr_auc": lr_cv_score
        },
        "Random Forest": {
            "model": rf_model,
            "cv_pr_auc": rf_cv_score
        },
        "XGBoost": {
            "model": xgb_model,
            "cv_pr_auc": xgb_cv_score
        }
    }

    logger.info("Completed training all candidate models.")
    return models_dict


def train_fraud_model(X_train: np.ndarray, y_train: pd.Series) -> Dict[str, Dict[str, Any]]:
    """Alias function for train_all_models."""
    return train_all_models(X_train, y_train)

