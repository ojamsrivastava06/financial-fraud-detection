"""
Model evaluation, comparison, confusion matrix plotting, ROC/PR curves,
threshold optimization, and feature importance module.
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score,
    accuracy_score,
    confusion_matrix,
    roc_curve,
    precision_recall_curve,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


def evaluate_single_model(
    model: Any,
    X_test: np.ndarray,
    y_test: pd.Series,
    threshold: float = 0.50
) -> Dict[str, Any]:
    """
    Evaluates model probabilities and predictions against test set metrics.
    """
    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= threshold).astype(int)

    pr_auc = float(average_precision_score(y_test, y_prob))
    roc_auc = float(roc_auc_score(y_test, y_prob))
    precision = float(precision_score(y_test, y_pred, zero_division=0))
    recall = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    accuracy = float(accuracy_score(y_test, y_pred))
    cm = confusion_matrix(y_test, y_pred).tolist()

    return {
        "y_prob": y_prob,
        "y_pred": y_pred,
        "test_pr_auc": round(pr_auc, 4),
        "test_roc_auc": round(roc_auc, 4),
        "test_precision": round(precision, 4),
        "test_recall": round(recall, 4),
        "test_f1": round(f1, 4),
        "test_accuracy": round(accuracy, 4),
        "confusion_matrix": cm,
    }


def plot_confusion_matrix(
    cm: List[List[int]],
    model_name: str,
    output_path: Path
) -> None:
    """Plot and save confusion matrix figure."""
    plt.figure(figsize=(6, 5))
    sns.set_theme(style="white")
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        cbar=False,
        xticklabels=["Legitimate (0)", "Fraudulent (1)"],
        yticklabels=["Legitimate (0)", "Fraudulent (1)"],
        annot_kws={"size": 14, "weight": "bold"}
    )
    plt.title(f"Confusion Matrix — {model_name}", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Predicted Class", fontsize=11)
    plt.ylabel("Actual Class", fontsize=11)
    plt.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved confusion matrix figure to {output_path}")


def plot_roc_pr_comparison(
    eval_results: Dict[str, Dict[str, Any]],
    y_test: pd.Series,
    output_dir: Path
) -> None:
    """Plot and save combined ROC and Precision-Recall comparison curves."""
    sns.set_theme(style="whitegrid")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. ROC Curves Plot
    plt.figure(figsize=(8, 6))
    for name, res in eval_results.items():
        fpr, tpr, _ = roc_curve(y_test, res["y_prob"])
        auc_val = res["test_roc_auc"]
        plt.plot(fpr, tpr, label=f"{name} (ROC-AUC = {auc_val:.4f})", linewidth=2)

    plt.plot([0, 1], [0, 1], "k--", label="Random Classifier", alpha=0.6)
    plt.xlabel("False Positive Rate", fontsize=12)
    plt.ylabel("True Positive Rate (Recall)", fontsize=12)
    plt.title("ROC Curve Comparison", fontsize=14, fontweight="bold")
    plt.legend(loc="lower right", fontsize=11)
    plt.tight_layout()

    roc_path = output_dir / "model_roc_comparison.png"
    plt.savefig(roc_path, dpi=300)
    plt.close()
    logger.info(f"Saved ROC comparison plot to {roc_path}")

    # 2. Precision-Recall Curves Plot
    plt.figure(figsize=(8, 6))
    for name, res in eval_results.items():
        precision, recall, _ = precision_recall_curve(y_test, res["y_prob"])
        pr_auc_val = res["test_pr_auc"]
        plt.plot(recall, precision, label=f"{name} (PR-AUC = {pr_auc_val:.4f})", linewidth=2)

    no_skill = y_test.mean()
    plt.axhline(y=no_skill, color="k", linestyle="--", label=f"No Skill Baseline ({no_skill:.3f})", alpha=0.6)
    plt.xlabel("Recall", fontsize=12)
    plt.ylabel("Precision", fontsize=12)
    plt.title("Precision-Recall Curve Comparison", fontsize=14, fontweight="bold")
    plt.legend(loc="lower left", fontsize=11)
    plt.tight_layout()

    pr_path = output_dir / "model_pr_comparison.png"
    plt.savefig(pr_path, dpi=300)
    plt.close()
    logger.info(f"Saved PR comparison plot to {pr_path}")


def analyze_decision_thresholds(
    y_test: pd.Series,
    y_prob: np.ndarray,
    model_name: str,
    output_csv_path: Path
) -> Tuple[pd.DataFrame, float]:
    """
    Evaluates operating thresholds from 0.05 to 0.95 and identifies recommended threshold.
    """
    thresholds = np.arange(0.05, 0.96, 0.05)
    records = []

    best_threshold = 0.50
    best_f1 = -1.0

    for th in thresholds:
        y_pred = (y_prob >= th).astype(int)
        cm = confusion_matrix(y_test, y_pred)
        tn, fp, fn, tp = cm.ravel()

        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

        if f1 > best_f1:
            best_f1 = f1
            best_threshold = th

        records.append({
            "threshold": round(float(th), 2),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1_score": round(float(f1), 4),
            "fraud_detection_rate": round(float(rec), 4),
            "false_positive_rate": round(float(fpr), 4),
            "true_positives": int(tp),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_negatives": int(tn)
        })

    df_th = pd.DataFrame(records)
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    df_th.to_csv(output_csv_path, index=False)
    logger.info(f"Threshold analysis for '{model_name}' saved to {output_csv_path}. Best F1 threshold: {best_threshold:.2f}")
    return df_th, round(float(best_threshold), 2)


def generate_feature_importance_report(
    model: Any,
    feature_names: List[str],
    output_csv_path: Path,
    output_fig_path: Path
) -> pd.DataFrame:
    """Extracts and plots feature importances or model coefficients."""
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    elif hasattr(model, "coef_"):
        importances = np.abs(model.coef_[0])
    else:
        logger.warning(f"Model {type(model).__name__} does not support feature_importances_ or coef_.")
        return pd.DataFrame()

    df_imp = pd.DataFrame({
        "feature": feature_names,
        "importance": importances
    }).sort_values(by="importance", ascending=False).reset_index(drop=True)

    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    df_imp.to_csv(output_csv_path, index=False)

    # Plot top 15 features
    plt.figure(figsize=(10, 6))
    sns.set_theme(style="whitegrid")
    top_df = df_imp.head(15)
    sns.barplot(data=top_df, x="importance", y="feature", palette="Blues_r")
    plt.title(f"Top 15 Feature Importance / Coefficient Weights ({type(model).__name__})", fontsize=13, fontweight="bold")
    plt.xlabel("Importance / Absolute Coefficient Weight", fontsize=11)
    plt.ylabel("Feature", fontsize=11)
    plt.tight_layout()

    output_fig_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_fig_path, dpi=300)
    plt.close()
    logger.info(f"Saved feature importance report to {output_csv_path} and figure to {output_fig_path}")

    return df_imp
