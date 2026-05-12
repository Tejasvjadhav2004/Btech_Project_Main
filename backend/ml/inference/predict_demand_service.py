"""
Demand Prediction Service - Inference service for demand forecasting

Loads trained models and generates demand predictions.
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ml.utils.artifact_manager import ArtifactManager, artifact_manager
from ml.preprocessing.feature_engineer import FeatureEngineer
from db.connection import mongodb

logger = logging.getLogger(__name__)


class DemandPredictionService:
    """
    Service for generating demand predictions.

    Loads trained models and makes predictions for future demand.
    """

    MODEL_NAME = "demand_forecast_model"
    COLLECTION_NAME = "predicted_demand"

    def __init__(self):
        self.artifact_manager = ArtifactManager()
        self.feature_engineer = FeatureEngineer()
        self.model = None
        self.feature_columns: List[str] = []
        self.model_metadata: Dict[str, Any] = {}
        self.encoders: Dict[str, Any] = {}

    @property
    def db(self):
        """Get database connection dynamically"""
        return mongodb.get_database()

    def load_model(self) -> bool:
        """
        Load the trained demand forecast model.

        Returns:
            True if model loaded successfully, False otherwise
        """
        try:
            if not self.artifact_manager.model_exists(self.MODEL_NAME):
                logger.warning(f"Model {self.MODEL_NAME} not found. Run training first.")
                return False

            artifact_bundle = self.artifact_manager.load_model(self.MODEL_NAME)
            self.model = artifact_bundle["model"]
            self.feature_columns = artifact_bundle.get("feature_columns", [])
            self.feature_engineer = artifact_bundle.get("feature_engineer", FeatureEngineer())
            self.encoders = artifact_bundle.get("encoders", {})

            self.model_metadata = self.artifact_manager.load_metadata(self.MODEL_NAME) or {}

            logger.info(f"Model loaded successfully with {len(self.feature_columns)} features")
            logger.info(f"Encoders loaded: {list(self.encoders.keys())}")
            return True

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False

    def predict_demand(
        self,
        sku: str,
        store_id: str,
        days_ahead: int = 7,
        historical_stats: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Predict future demand for a SKU at a store.

        Args:
            sku: Product SKU
            store_id: Store ID
            days_ahead: Number of days to predict
            historical_stats: Optional historical statistics for features

        Returns:
            Prediction result with demand, confidence, and trend
        """
        if self.model is None:
            if not self.load_model():
                raise RuntimeError("Model not loaded. Run training first.")

        try:
            # Get historical data from database
            if historical_stats is None:
                historical_stats = self._get_historical_stats(sku, store_id)

            # Get last date from historical data
            last_date = historical_stats.get("last_date")
            if last_date:
                last_date = pd.Timestamp(last_date)
            else:
                last_date = pd.Timestamp.now() - timedelta(days=1)

            # Create features for future dates - pass required features from model
            future_features = self.feature_engineer.create_future_features(
                last_date=last_date,
                days_ahead=days_ahead,
                sku=sku,
                store_id=store_id,
                historical_stats=historical_stats,
                required_features=self.feature_columns
            )

            # Add encoded features if encoders are available
            if 'sku_encoder' in self.encoders:
                try:
                    future_features['sku_encoded'] = self.encoders['sku_encoder'].transform([str(sku)])[0]
                except ValueError:
                    # Handle unknown SKU
                    future_features['sku_encoded'] = -1

            if 'store_encoder' in self.encoders:
                try:
                    future_features['store_encoded'] = self.encoders['store_encoder'].transform([str(store_id)])[0]
                except ValueError:
                    future_features['store_encoded'] = -1

            if 'wh_encoder' in self.encoders:
                future_features['warehouse_encoded'] = 0  # Default

            if 'cat_encoder' in self.encoders:
                future_features['category_encoded'] = 0  # Default

            # Reorder columns to match training order exactly
            X = future_features[self.feature_columns].fillna(0)

            # Make predictions
            predictions = self.model.predict(X)

            # Calculate statistics
            total_predicted = float(np.sum(predictions))
            mean_predicted = float(np.mean(predictions))
            std_predicted = float(np.std(predictions))

            # Determine trend
            if len(predictions) > 1:
                trend_value = predictions[-1] - predictions[0]
                if trend_value > 0.1 * mean_predicted:
                    trend = "increasing"
                elif trend_value < -0.1 * mean_predicted:
                    trend = "decreasing"
                else:
                    trend = "stable"
            else:
                trend = "stable"

            # Calculate confidence (based on model R2 and prediction variance)
            model_r2 = self.model_metadata.get("metrics", {}).get("R2", 0.5)
            confidence = min(0.95, max(0.5, model_r2 * (1 - std_predicted / (mean_predicted + 1))))

            result = {
                "sku": sku,
                "store_id": store_id,
                "prediction_window_days": days_ahead,
                "predicted_demand": round(total_predicted),
                "predicted_daily_avg": round(mean_predicted, 2),
                "predicted_demand_7d": round(total_predicted, 2) if days_ahead == 7 else round(mean_predicted * 7, 2),
                "confidence": round(confidence, 2),
                "trend": trend,
                "daily_predictions": [round(float(p), 2) for p in predictions],
                "model_type": self.model_metadata.get("model_type", "unknown"),
                "generated_at": datetime.utcnow().isoformat()
            }

            return result

        except Exception as e:
            logger.error(f"Error predicting demand for {sku}-{store_id}: {e}")
            raise

    def _get_historical_stats(self, sku: str, store_id: str) -> Dict[str, Any]:
        """
        Get historical statistics from the database.

        Args:
            sku: Product SKU
            store_id: Store ID

        Returns:
            Dictionary of historical statistics
        """
        try:
            # Query transactions collection
            collection = self.db["transactions"]

            # Find recent transactions for this SKU-Store
            pipeline = [
                {"$match": {"sku": sku, "location_id": store_id}},
                {"$sort": {"timestamp": -1}},
                {"$limit": 90},  # Last 90 transactions
                {"$group": {
                    "_id": None,
                    "mean_quantity": {"$avg": "$quantity"},
                    "std_quantity": {"$stdDevPop": "$quantity"},
                    "min_quantity": {"$min": "$quantity"},
                    "max_quantity": {"$max": "$quantity"},
                    "total_transactions": {"$sum": 1},
                    "last_date": {"$max": "$timestamp"}
                }}
            ]

            result = list(collection.aggregate(pipeline))

            if result:
                stats = result[0]
                return {
                    "mean_quantity": stats.get("mean_quantity", 5),
                    "std_quantity": stats.get("std_quantity", 2),
                    "min_quantity": stats.get("min_quantity", 0),
                    "max_quantity": stats.get("max_quantity", 20),
                    "transaction_count": stats.get("total_transactions", 0),
                    "last_date": stats.get("last_date"),
                    "rolling_mean_7": stats.get("mean_quantity", 5),
                    "rolling_mean_14": stats.get("mean_quantity", 5),
                    "rolling_mean_28": stats.get("mean_quantity", 5),
                    "rolling_std_7": stats.get("std_quantity", 2),
                    "rolling_std_14": stats.get("std_quantity", 2),
                    "rolling_std_28": stats.get("std_quantity", 2)
                }

            return self._get_default_stats()

        except Exception as e:
            logger.warning(f"Could not get historical stats: {e}")
            return self._get_default_stats()

    def _get_default_stats(self) -> Dict[str, Any]:
        """Get default statistics when no historical data available"""
        return {
            "mean_quantity": 5,
            "std_quantity": 2,
            "min_quantity": 0,
            "max_quantity": 20,
            "transaction_count": 0,
            "last_date": None,
            "rolling_mean_7": 5,
            "rolling_mean_14": 5,
            "rolling_mean_28": 5,
            "rolling_std_7": 2,
            "rolling_std_14": 2,
            "rolling_std_28": 2
        }

    def predict_batch(
        self,
        items: List[Dict[str, str]],
        days_ahead: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Predict demand for multiple SKU-Store combinations.

        Args:
            items: List of dicts with 'sku' and 'store_id' keys
            days_ahead: Number of days to predict

        Returns:
            List of prediction results
        """
        results = []

        for item in items:
            sku = item.get("sku")
            store_id = item.get("store_id")

            if not sku or not store_id:
                continue

            try:
                prediction = self.predict_demand(sku, store_id, days_ahead)
                results.append(prediction)
            except Exception as e:
                logger.error(f"Error in batch prediction for {sku}-{store_id}: {e}")
                results.append({
                    "sku": sku,
                    "store_id": store_id,
                    "error": str(e)
                })

        return results

    def save_predictions_to_db(
        self,
        predictions: List[Dict[str, Any]]
    ) -> int:
        """
        Save predictions to MongoDB.

        Args:
            predictions: List of prediction results

        Returns:
            Number of predictions saved
        """
        if not predictions:
            return 0

        collection = self.db[self.COLLECTION_NAME]

        saved_count = 0
        for pred in predictions:
            if "error" in pred:
                continue

            # Add timestamp
            pred["generated_at"] = datetime.utcnow()

            # Upsert by sku-store_id combination
            filter_query = {
                "sku": pred["sku"],
                "store_id": pred["store_id"]
            }

            result = collection.update_one(
                filter_query,
                {"$set": pred},
                upsert=True
            )

            if result.upserted_id or result.modified_count:
                saved_count += 1

        logger.info(f"Saved {saved_count} predictions to database")
        return saved_count

    def get_predictions(
        self,
        sku: Optional[str] = None,
        store_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get saved predictions from database.

        Args:
            sku: Optional SKU filter
            store_id: Optional store ID filter
            limit: Maximum number of results

        Returns:
            List of predictions
        """
        collection = self.db[self.COLLECTION_NAME]

        query = {}
        if sku:
            query["sku"] = sku
        if store_id:
            query["store_id"] = store_id

        predictions = list(collection.find(query, {"_id": 0}).sort("generated_at", -1).limit(limit))

        return predictions

    def generate_all_predictions(
        self,
        days_ahead: int = 7
    ) -> Dict[str, Any]:
        """
        Generate predictions for all active inventory items.

        Args:
            days_ahead: Number of days to predict

        Returns:
            Summary of prediction generation
        """
        start_time = datetime.utcnow()

        # Get all active SKU-Store combinations from inventory
        inventory = list(self.db.inventory.find({}, {"sku": 1, "location_id": 1, "location_type": 1}))

        # Get unique combinations (focus on store-level predictions)
        items = set()
        for item in inventory:
            sku = item.get("sku")
            location_id = item.get("location_id")
            if sku and location_id:
                items.add((sku, location_id))

        items = [{"sku": sku, "store_id": store_id} for sku, store_id in items]

        logger.info(f"Generating predictions for {len(items)} SKU-Store combinations")

        # Generate predictions
        predictions = self.predict_batch(list(items)[:200], days_ahead)  # Limit to 200 for performance

        # Save to database
        saved_count = self.save_predictions_to_db(predictions)

        elapsed = (datetime.utcnow() - start_time).total_seconds()

        return {
            "total_items": len(items),
            "predictions_generated": len(predictions),
            "predictions_saved": saved_count,
            "elapsed_seconds": elapsed,
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_high_demand_items(self, threshold: int = 50) -> List[Dict[str, Any]]:
        """
        Get items with predicted high demand.

        Args:
            threshold: Minimum predicted demand threshold

        Returns:
            List of high-demand predictions
        """
        collection = self.db[self.COLLECTION_NAME]

        query = {"predicted_demand_7d": {"$gte": threshold}}
        predictions = list(collection.find(query, {"_id": 0}).sort("predicted_demand_7d", -1))

        return predictions


demand_prediction_service = DemandPredictionService()
