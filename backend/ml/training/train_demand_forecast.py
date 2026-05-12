"""
Demand Forecast Trainer - Training pipeline for demand forecasting model

Trains a machine learning model to predict future product demand.
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import numpy as np
import pandas as pd
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ml.preprocessing.data_processor import DataProcessor, data_processor
from ml.preprocessing.feature_engineer import FeatureEngineer, feature_engineer
from ml.evaluation.model_evaluator import ModelEvaluator, model_evaluator
from ml.utils.artifact_manager import ArtifactManager, artifact_manager

logger = logging.getLogger(__name__)


class DemandForecastTrainer:
    """
    Training pipeline for demand forecasting.

    Uses Random Forest or XGBoost for demand prediction.
    """

    def __init__(
        self,
        model_type: str = "random_forest",
        data_path: Optional[Path] = None,
        test_size: float = 0.2
    ):
        """
        Initialize the trainer.

        Args:
            model_type: Type of model ('random_forest' or 'xgboost')
            data_path: Path to the transaction data CSV
            test_size: Proportion of data for testing
        """
        self.model_type = model_type
        self.test_size = test_size
        self.data_processor = DataProcessor(data_path)
        self.feature_engineer = FeatureEngineer()
        self.evaluator = ModelEvaluator()
        self.artifact_manager = ArtifactManager()

        self.model = None
        self.scaler = None
        self.feature_columns: List[str] = []
        self.training_metadata: Dict[str, Any] = {}

    def train(
        self,
        aggregate_by_sku_store: bool = True
    ) -> Dict[str, Any]:
        """
        Run the complete training pipeline.

        Steps:
        1. Load and preprocess data
        2. Create features
        3. Split into train/test
        4. Train model
        5. Evaluate model
        6. Save artifacts

        Args:
            aggregate_by_sku_store: Whether to aggregate data by SKU-Store-Date

        Returns:
            Training results including metrics
        """
        logger.info(f"Starting demand forecast training with {self.model_type}")
        start_time = datetime.utcnow()

        # Step 1: Load and preprocess data
        logger.info("Step 1: Loading and preprocessing data...")
        raw_df = self.data_processor.load_data()
        df = self.data_processor.preprocess(raw_df)

        if aggregate_by_sku_store:
            df = self.data_processor.aggregate_by_sku_store_date(df)

        # Step 2: Create features
        logger.info("Step 2: Creating features...")
        df = self.feature_engineer.create_features(
            df,
            date_column='date' if 'date' in df.columns else 'transaction_date',
            target_column='quantity_sold'
        )

        # Store feature columns before filtering
        self.feature_columns = self.feature_engineer.get_feature_columns()

        # Step 3: Prepare training data
        logger.info("Step 3: Preparing training data...")
        X, y = self._prepare_training_data(df)

        # Split data
        X_train, X_test, y_train, y_test = self._split_data(X, y)

        # Step 4: Train model
        logger.info("Step 4: Training model...")
        self.model = self._create_model()
        self.model.fit(X_train, y_train)

        # Log training performance
        train_score = self.model.score(X_train, y_train)
        logger.info(f"Training R² Score: {train_score:.4f}")

        # Step 5: Evaluate model
        logger.info("Step 5: Evaluating model...")
        y_pred = self.model.predict(X_test)
        metrics = self.evaluator.evaluate(y_test, y_pred, self.model_type)

        # Feature importance
        feature_importance = self.evaluator.feature_importance_analysis(
            self.model, self.feature_columns
        )

        # Step 6: Save artifacts
        logger.info("Step 6: Saving model artifacts...")
        model_path = self._save_artifacts(metrics, feature_importance)

        # Training summary
        training_time = (datetime.utcnow() - start_time).total_seconds()

        results = {
            "model_type": self.model_type,
            "model_path": str(model_path),
            "metrics": metrics,
            "feature_importance": feature_importance[:10] if isinstance(feature_importance, list) else dict(list(feature_importance.items())[:10]),
            "training_time_seconds": training_time,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "feature_count": len(self.feature_columns),
            "timestamp": datetime.utcnow().isoformat()
        }

        self.training_metadata = results

        logger.info(f"Training complete in {training_time:.2f} seconds")
        logger.info(f"Model saved to: {model_path}")

        return results

    def _prepare_training_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare feature matrix and target vector.

        Args:
            df: DataFrame with features

        Returns:
            Tuple of (X, y)
        """
        # Create SKU and Store numeric encodings (these help capture product/store specific patterns)
        from sklearn.preprocessing import LabelEncoder

        # Encode SKU and Store if present
        if 'sku' in df.columns:
            sku_encoder = LabelEncoder()
            df['sku_encoded'] = sku_encoder.fit_transform(df['sku'].astype(str))
            self.sku_encoder = sku_encoder

        if 'store_id' in df.columns:
            store_encoder = LabelEncoder()
            df['store_encoded'] = store_encoder.fit_transform(df['store_id'].astype(str))
            self.store_encoder = store_encoder

        if 'warehouse_id' in df.columns:
            wh_encoder = LabelEncoder()
            df['warehouse_encoded'] = wh_encoder.fit_transform(df['warehouse_id'].astype(str))
            self.wh_encoder = wh_encoder

        if 'product_category' in df.columns:
            cat_encoder = LabelEncoder()
            df['category_encoded'] = cat_encoder.fit_transform(df['product_category'].astype(str))
            self.cat_encoder = cat_encoder

        # Define columns to exclude (these are not available for future predictions)
        exclude_cols = [
            'transaction_date', 'date', 'quantity_sold', 'total_sales',
            'sku', 'store_id', 'warehouse_id', 'product_category', 'supplier_name',
            'expected_delivery_date', 'actual_delivery_date', 'delivery_status',
            'delivery_status_encoded',
            # Exclude columns that won't be available for future predictions
            'avg_unit_price', 'delay_rate', 'reorder_threshold'
        ]

        # Get feature columns
        feature_cols = [col for col in df.columns if col not in exclude_cols]

        # Remove any non-numeric columns
        numeric_cols = df[feature_cols].select_dtypes(include=[np.number]).columns.tolist()

        # Sort feature columns for consistency
        numeric_cols = sorted(numeric_cols)

        self.feature_columns = numeric_cols

        X = df[numeric_cols].fillna(0)
        y = df['quantity_sold'].fillna(0)

        logger.info(f"Using {len(numeric_cols)} features for training")
        logger.debug(f"Features: {numeric_cols}")

        return X, y

    def _split_data(
        self,
        X: pd.DataFrame,
        y: pd.Series
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        Split data into training and test sets.

        Uses time-based split to avoid data leakage.

        Args:
            X: Feature matrix
            y: Target vector

        Returns:
            Tuple of (X_train, X_test, y_train, y_test)
        """
        split_idx = int(len(X) * (1 - self.test_size))

        X_train = X.iloc[:split_idx].copy()
        X_test = X.iloc[split_idx:].copy()
        y_train = y.iloc[:split_idx].copy()
        y_test = y.iloc[split_idx:].copy()

        return X_train, X_test, y_train, y_test

    def _create_model(self):
        """
        Create the ML model based on model_type.

        Returns:
            Configured model instance
        """
        if self.model_type == "xgboost":
            try:
                from xgboost import XGBRegressor

                model = XGBRegressor(
                    n_estimators=300,
                    max_depth=8,
                    learning_rate=0.05,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    min_child_weight=3,
                    random_state=42,
                    n_jobs=-1
                )
            except ImportError:
                logger.warning("XGBoost not installed, falling back to Random Forest")
                self.model_type = "random_forest"
                return self._create_model()

        elif self.model_type == "random_forest":
            from sklearn.ensemble import RandomForestRegressor

            model = RandomForestRegressor(
                n_estimators=200,
                max_depth=15,
                min_samples_split=3,
                min_samples_leaf=1,
                max_features='sqrt',
                random_state=42,
                n_jobs=-1
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

        return model

    def _save_artifacts(
        self,
        metrics: Dict[str, float],
        feature_importance: Dict[str, float]
    ) -> Path:
        """
        Save model and metadata to disk.

        Args:
            metrics: Evaluation metrics
            feature_importance: Feature importance scores

        Returns:
            Path to saved model
        """
        # Get encoders if they exist
        encoders = {}
        if hasattr(self, 'sku_encoder'):
            encoders['sku_encoder'] = self.sku_encoder
        if hasattr(self, 'store_encoder'):
            encoders['store_encoder'] = self.store_encoder
        if hasattr(self, 'wh_encoder'):
            encoders['wh_encoder'] = self.wh_encoder
        if hasattr(self, 'cat_encoder'):
            encoders['cat_encoder'] = self.cat_encoder

        artifact_bundle = {
            "model": self.model,
            "feature_columns": self.feature_columns,
            "feature_engineer": self.feature_engineer,
            "encoders": encoders
        }

        metadata = {
            "model_type": self.model_type,
            "metrics": metrics,
            "feature_importance": feature_importance,
            "feature_count": len(self.feature_columns),
            "training_date": datetime.utcnow().isoformat()
        }

        # Save as latest model
        model_path = self.artifact_manager.save_latest_model(
            artifact_bundle,
            "demand_forecast_model",
            metadata
        )

        return model_path

    def train_per_sku_store(self, top_n: int = 50) -> Dict[str, Any]:
        """
        Train individual models for top SKU-Store combinations.

        This creates specialized models that perform better for
        high-volume products.

        Args:
            top_n: Number of top SKU-Store combinations to train for

        Returns:
            Training summary
        """
        logger.info(f"Training individual models for top {top_n} SKU-Store combinations")

        # Load and process data
        raw_df = self.data_processor.load_data()
        df = self.data_processor.preprocess(raw_df)

        # Find top SKU-Store by volume
        volume_df = df.groupby(['sku', 'store_id'])['quantity_sold'].sum().reset_index()
        volume_df = volume_df.sort_values('quantity_sold', ascending=False).head(top_n)

        results = {
            "models_trained": 0,
            "failed": 0,
            "details": []
        }

        for _, row in volume_df.iterrows():
            sku = row['sku']
            store_id = row['store_id']

            try:
                # Get data for this SKU-Store
                sku_store_df = self.data_processor.get_data_for_sku_store(sku, store_id, df)

                if len(sku_store_df) < 30:
                    logger.warning(f"Skipping {sku}-{store_id}: insufficient data")
                    continue

                # Create features
                sku_store_df = self.feature_engineer.create_features(sku_store_df)

                # Prepare and train
                X, y = self._prepare_training_data(sku_store_df)

                if len(X) < 20:
                    continue

                X_train, X_test, y_train, y_test = self._split_data(X, y)

                model = self._create_model()
                model.fit(X_train, y_train)

                y_pred = model.predict(X_test)
                metrics = self.evaluator.evaluate(y_test, y_pred, f"{sku}-{store_id}")

                # Save model
                artifact_bundle = {
                    "model": model,
                    "feature_columns": self.feature_columns
                }

                self.artifact_manager.save_model(
                    artifact_bundle,
                    f"demand_model_{sku}_{store_id}",
                    {"sku": sku, "store_id": store_id, "metrics": metrics}
                )

                results["models_trained"] += 1
                results["details"].append({
                    "sku": sku,
                    "store_id": store_id,
                    "samples": len(X),
                    "metrics": metrics
                })

            except Exception as e:
                logger.error(f"Error training model for {sku}-{store_id}: {e}")
                results["failed"] += 1

        logger.info(f"Trained {results['models_trained']} SKU-Store specific models")
        return results


def run_training():
    """Run the demand forecast training pipeline"""
    trainer = DemandForecastTrainer(model_type="random_forest")
    results = trainer.train()
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = run_training()
    print("\n" + "="*50)
    print("Training Results:")
    print("="*50)
    for key, value in results.items():
        if key != "feature_importance":
            print(f"{key}: {value}")
