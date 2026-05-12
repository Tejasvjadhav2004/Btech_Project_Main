"""
Model Evaluator - Evaluates ML model performance

Provides metrics and visualization for model evaluation.
"""
import numpy as np
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class ModelEvaluator:
    """Evaluates regression model performance"""

    def __init__(self):
        self.metrics: Dict[str, float] = {}

    def evaluate(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        model_name: str = "model"
    ) -> Dict[str, float]:
        """
        Calculate regression metrics.

        Args:
            y_true: Actual values
            y_pred: Predicted values
            model_name: Name of the model for logging

        Returns:
            Dictionary of metric names and values
        """
        y_true = np.array(y_true).flatten()
        y_pred = np.array(y_pred).flatten()

        # Ensure same length
        min_len = min(len(y_true), len(y_pred))
        y_true = y_true[:min_len]
        y_pred = y_pred[:min_len]

        # Calculate metrics
        mae = self._mean_absolute_error(y_true, y_pred)
        mse = self._mean_squared_error(y_true, y_pred)
        rmse = self._root_mean_squared_error(y_true, y_pred)
        r2 = self._r2_score(y_true, y_pred)
        mape = self._mean_absolute_percentage_error(y_true, y_pred)

        self.metrics = {
            "MAE": mae,
            "MSE": mse,
            "RMSE": rmse,
            "R2": r2,
            "MAPE": mape
        }

        logger.info(f"{model_name} Evaluation Metrics:")
        logger.info(f"  MAE: {mae:.4f}")
        logger.info(f"  RMSE: {rmse:.4f}")
        logger.info(f"  R²: {r2:.4f}")
        logger.info(f"  MAPE: {mape:.2f}%")

        return self.metrics

    def _mean_absolute_error(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calculate Mean Absolute Error"""
        return float(np.mean(np.abs(y_true - y_pred)))

    def _mean_squared_error(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calculate Mean Squared Error"""
        return float(np.mean((y_true - y_pred) ** 2))

    def _root_mean_squared_error(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calculate Root Mean Squared Error"""
        return float(np.sqrt(self._mean_squared_error(y_true, y_pred)))

    def _r2_score(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calculate R-squared (coefficient of determination)"""
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)

        if ss_tot == 0:
            return 0.0

        return float(1 - (ss_res / ss_tot))

    def _mean_absolute_percentage_error(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> float:
        """Calculate Mean Absolute Percentage Error"""
        # Avoid division by zero
        mask = y_true != 0
        if not mask.any():
            return 0.0

        mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
        return float(mape)

    def get_metrics(self) -> Dict[str, float]:
        """Get last calculated metrics"""
        return self.metrics.copy()

    def compare_models(
        self,
        results: Dict[str, Dict[str, float]]
    ) -> Dict[str, Any]:
        """
        Compare multiple models.

        Args:
            results: Dict mapping model names to their metrics

        Returns:
            Comparison summary with best model
        """
        comparison = {
            "models": results,
            "best_by_metric": {},
            "recommendation": None
        }

        # Find best model for each metric
        metrics_to_compare = ["MAE", "RMSE", "R2", "MAPE"]

        for metric in metrics_to_compare:
            if metric == "R2":
                # Higher is better for R2
                best_model = max(
                    results.keys(),
                    key=lambda x: results[x].get(metric, -float('inf'))
                )
            else:
                # Lower is better for error metrics
                best_model = min(
                    results.keys(),
                    key=lambda x: results[x].get(metric, float('inf'))
                )

            comparison["best_by_metric"][metric] = {
                "model": best_model,
                "value": results[best_model].get(metric)
            }

        # Overall recommendation (based on RMSE and R2)
        rmse_ranking = sorted(
            results.keys(),
            key=lambda x: results[x].get("RMSE", float('inf'))
        )
        r2_ranking = sorted(
            results.keys(),
            key=lambda x: results[x].get("R2", -float('inf')),
            reverse=True
        )

        # Simple average of rankings
        avg_rank = {}
        for model in results.keys():
            avg_rank[model] = (rmse_ranking.index(model) + r2_ranking.index(model)) / 2

        best_overall = min(avg_rank.keys(), key=lambda x: avg_rank[x])
        comparison["recommendation"] = best_overall

        return comparison

    def confidence_interval(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        confidence: float = 0.95
    ) -> Dict[str, float]:
        """
        Calculate prediction confidence interval.

        Args:
            y_true: Actual values
            y_pred: Predicted values
            confidence: Confidence level (0.0 to 1.0)

        Returns:
            Dict with lower and upper bounds
        """
        from scipy import stats

        errors = y_true - y_pred
        std_error = np.std(errors)

        z_score = stats.norm.ppf((1 + confidence) / 2)

        return {
            "lower_bound": float(-z_score * std_error),
            "upper_bound": float(z_score * std_error),
            "std_error": float(std_error),
            "confidence_level": confidence
        }

    def feature_importance_analysis(
        self,
        model,
        feature_names: List[str]
    ) -> Dict[str, float]:
        """
        Analyze feature importance for tree-based models.

        Args:
            model: Trained model with feature_importances_ attribute
            feature_names: List of feature names

        Returns:
            Dict mapping feature names to importance scores
        """
        if not hasattr(model, 'feature_importances_'):
            logger.warning("Model does not have feature_importances_ attribute")
            return {}

        importances = model.feature_importances_

        importance_dict = dict(zip(feature_names, importances))

        # Sort by importance
        sorted_importance = dict(
            sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
        )

        return sorted_importance


model_evaluator = ModelEvaluator()
