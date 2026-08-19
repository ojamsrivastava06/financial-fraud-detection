"""
Model Training and Serialization Script.
Executes stratified train/test split, fits preprocessing pipeline on train set only,
trains and cross-validates Logistic Regression, Random Forest, and XGBoost models,
evaluates test-set metrics, optimizes decision thresholds, generates report figures,
selects winning model based on PR-AUC, and serializes model artifacts.
"""

from pathlib import Path
import sys
import json
import datetime
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config.settings import settings
from src.features.engineering import build_features
from src.features.feature_pipeline import create_preprocessing_pipeline
from src.models.train import train_all_models, RANDOM_STATE
from src.models.evaluate import (
    evaluate_single_model,
    plot_confusion_matrix,
    plot_roc_pr_comparison,
    analyze_decision_thresholds,
    generate_feature_importance_report,
)
from src.models.model_registry import ModelRegistry
from src.models.predict import predict_fraud_probability
from src.utils.logger import get_logger

logger = get_logger(__name__)


def run_training_pipeline():
    """Executes full Phase 3 model training pipeline."""
    logger.info("==================================================")
    logger.info("STARTING PHASE 3 MODEL TRAINING & EVALUATION PIPELINE")
    logger.info("==================================================")

    # 1. Load Processed Dataset
    data_path = settings.BASE_DIR / "data" / "processed" / "financial_fraud_processed.csv"
    if not data_path.exists():
        logger.error(f"Processed dataset not found at {data_path}. Running feature pipeline...")
        from scripts.run_pipeline import run_full_pipeline
        run_full_pipeline()

    df = pd.read_csv(data_path)
    logger.info(f"Loaded processed dataset with shape: {df.shape}")

    target_col = "Fraudulent"
    drop_cols = ["Transaction_ID", "Customer_ID", "Transaction_Date", "Suspicious_Keyword", "Is_International", target_col]
    feature_cols = [c for c in df.columns if c not in drop_cols]

    X = df[feature_cols].copy()
    y = df[target_col].copy()

    # 2. Stratified 80/20 Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=RANDOM_STATE
    )
    logger.info(f"Train set: {len(X_train)} samples ({y_train.sum()} fraud). Test set: {len(X_test)} samples ({y_test.sum()} fraud).")

    # 3. Fit Preprocessing Pipeline ONLY on Training Set
    preprocessor = create_preprocessing_pipeline()
    X_train_proc = preprocessor.fit_transform(X_train)
    X_test_proc = preprocessor.transform(X_test)
    logger.info(f"Fitted ColumnTransformer. Transformed feature matrix shape: {X_train_proc.shape}")

    # Extract transformed feature names for importance mapping
    cat_encoder = preprocessor.named_transformers_["cat"].named_steps["onehot"]
    cat_cols = preprocessor.transformers[1][2]
    cat_feature_names = list(cat_encoder.get_feature_names_out(cat_cols))
    num_cols = preprocessor.transformers[0][2]
    bin_cols = preprocessor.transformers[2][2]
    all_transformed_feature_names = list(num_cols) + cat_feature_names + list(bin_cols)

    # 4. Train & Cross-Validate Candidate Models
    models_dict = train_all_models(X_train_proc, y_train)

    # 5. Evaluate Candidate Models on Test Set
    eval_results = {}
    comparison_records = []
    fig_dir = settings.BASE_DIR / "reports" / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    for name, item in models_dict.items():
        model = item["model"]
        cv_score = item["cv_pr_auc"]
        res = evaluate_single_model(model, X_test_proc, y_test)
        eval_results[name] = res

        record = {
            "model": name,
            "cv_pr_auc": round(cv_score, 4),
            "test_pr_auc": res["test_pr_auc"],
            "test_roc_auc": res["test_roc_auc"],
            "test_precision": res["test_precision"],
            "test_recall": res["test_recall"],
            "test_f1": res["test_f1"],
            "test_accuracy": res["test_accuracy"]
        }
        comparison_records.append(record)

        # Plot Individual Confusion Matrix
        cm_filename = f"{name.lower().replace(' ', '_')}_confusion_matrix.png"
        plot_confusion_matrix(res["confusion_matrix"], name, fig_dir / cm_filename)

    # Save Model Comparison CSV
    df_comp = pd.DataFrame(comparison_records).sort_values(by="test_pr_auc", ascending=False).reset_index(drop=True)
    comp_csv_path = settings.BASE_DIR / "reports" / "model_reports" / "model_comparison.csv"
    comp_csv_path.parent.mkdir(parents=True, exist_ok=True)
    df_comp.to_csv(comp_csv_path, index=False)
    logger.info(f"Saved model comparison report to {comp_csv_path}")

    # Plot ROC & PR Comparison Curves
    plot_roc_pr_comparison(eval_results, y_test, fig_dir)

    # 6. Select Best Model Based on PR-AUC
    best_model_name = df_comp.iloc[0]["model"]
    best_model = models_dict[best_model_name]["model"]
    best_eval = eval_results[best_model_name]
    logger.info(f"🏆 Best Winning Model Selected: {best_model_name} (Test PR-AUC: {best_eval['test_pr_auc']:.4f})")

    # 7. Threshold Optimization for Winning Model
    th_csv_path = settings.BASE_DIR / "reports" / "model_reports" / "threshold_analysis.csv"
    df_th, selected_threshold = analyze_decision_thresholds(
        y_test, best_eval["y_prob"], best_model_name, th_csv_path
    )

    # 8. Feature Importance Report (if applicable)
    imp_csv_path = settings.BASE_DIR / "reports" / "model_reports" / "feature_importance.csv"
    imp_fig_path = fig_dir / "feature_importance.png"
    generate_feature_importance_report(
        best_model, all_transformed_feature_names, imp_csv_path, imp_fig_path
    )

    # 9. Model Metadata Construction
    metadata = {
        "model_name": best_model_name,
        "model_version": "1.0.0",
        "training_datetime": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "dataset_name": "financial_fraud_processed.csv",
        "training_rows": len(X_train),
        "testing_rows": len(X_test),
        "raw_feature_count": len(feature_cols),
        "transformed_feature_count": X_train_proc.shape[1],
        "feature_names": feature_cols,
        "transformed_feature_names": all_transformed_feature_names,
        "target_name": target_col,
        "random_state": RANDOM_STATE,
        "cross_validation": "5-Fold StratifiedKFold",
        "test_metrics": {
            "cv_pr_auc": float(models_dict[best_model_name]["cv_pr_auc"]),
            "test_pr_auc": best_eval["test_pr_auc"],
            "test_roc_auc": best_eval["test_roc_auc"],
            "test_precision": best_eval["test_precision"],
            "test_recall": best_eval["test_recall"],
            "test_f1": best_eval["test_f1"],
            "test_accuracy": best_eval["test_accuracy"]
        },
        "selected_threshold": selected_threshold,
        "risk_thresholds": {
            "low_risk": 0.35,
            "medium_risk": 0.35,
            "high_risk": 0.65
        },
        "class_imbalance_strategy": "Class-weighted loss / scale_pos_weight tuning"
    }

    # 10. Serialize Artifacts to ModelRegistry
    registry = ModelRegistry()
    m_path, p_path, meta_path = registry.save_model_artifacts(
        model=best_model,
        preprocessor=preprocessor,
        metadata=metadata
    )

    # 11. Verify Test Inference Reload
    sample_tx = df_test = X_test.iloc[0].to_dict()
    pred_res = predict_fraud_probability(sample_tx)
    logger.info(f"Sample test prediction output verified: {pred_res}")

    logger.info("==================================================")
    logger.info("PHASE 3 MODEL TRAINING COMPLETED SUCCESSFULLY")
    logger.info("==================================================")


if __name__ == "__main__":
    run_training_pipeline()
