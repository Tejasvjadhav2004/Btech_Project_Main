"""
Artifact Manager - Manages ML model artifacts (save/load)

Handles serialization and persistence of trained models, scalers, and encoders.
"""
import os
import pickle
import json
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ArtifactManager:
    """Manages ML model artifacts with versioning support"""

    ARTIFACTS_DIR = Path(__file__).parent.parent / "artifacts"

    def __init__(self, artifacts_dir: Optional[Path] = None):
        self.artifacts_dir = artifacts_dir or self.ARTIFACTS_DIR
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def save_model(
        self,
        model: Any,
        name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Save a trained model to disk.

        Args:
            model: The trained model object
            name: Name for the model file (without extension)
            metadata: Optional metadata to save alongside the model

        Returns:
            Path to the saved model
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.pkl"
        filepath = self.artifacts_dir / filename

        with open(filepath, 'wb') as f:
            pickle.dump(model, f)

        if metadata:
            meta_filepath = filepath.with_suffix('.json')
            with open(meta_filepath, 'w') as f:
                json.dump({
                    **metadata,
                    "saved_at": datetime.utcnow().isoformat(),
                    "filename": filename
                }, f, indent=2, default=str)

        logger.info(f"Model saved to {filepath}")
        return filepath

    def save_latest_model(
        self,
        model: Any,
        name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Save model as the latest version (overwrites previous latest).

        Args:
            model: The trained model object
            name: Name for the model (e.g., 'demand_forecast_model')
            metadata: Optional metadata

        Returns:
            Path to the saved model
        """
        filepath = self.artifacts_dir / f"{name}.pkl"

        with open(filepath, 'wb') as f:
            pickle.dump(model, f)

        if metadata:
            meta_filepath = filepath.with_suffix('.json')
            with open(meta_filepath, 'w') as f:
                json.dump({
                    **metadata,
                    "saved_at": datetime.utcnow().isoformat(),
                    "filename": f"{name}.pkl"
                }, f, indent=2, default=str)

        logger.info(f"Latest model saved to {filepath}")
        return filepath

    def load_model(self, name: str, use_latest: bool = True) -> Any:
        """
        Load a trained model from disk.

        Args:
            name: Name of the model file (without extension)
            use_latest: If True, loads the latest version; if False, requires full name

        Returns:
            The loaded model object
        """
        if use_latest:
            filepath = self.artifacts_dir / f"{name}.pkl"
        else:
            filepath = self.artifacts_dir / f"{name}"

        if not filepath.exists():
            raise FileNotFoundError(f"Model not found: {filepath}")

        with open(filepath, 'rb') as f:
            model = pickle.load(f)

        logger.info(f"Model loaded from {filepath}")
        return model

    def load_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """Load metadata for a model"""
        meta_filepath = self.artifacts_dir / f"{name}.json"

        if not meta_filepath.exists():
            return None

        with open(meta_filepath, 'r') as f:
            return json.load(f)

    def model_exists(self, name: str) -> bool:
        """Check if a model exists"""
        filepath = self.artifacts_dir / f"{name}.pkl"
        return filepath.exists()

    def list_models(self) -> list:
        """List all saved models"""
        models = []
        for file in self.artifacts_dir.glob("*.pkl"):
            metadata = self.load_metadata(file.stem)
            models.append({
                "filename": file.name,
                "path": str(file),
                "metadata": metadata
            })
        return models

    def cleanup_old_versions(self, keep_latest: int = 3):
        """Remove old model versions, keeping only the latest ones"""
        all_models = sorted(
            self.artifacts_dir.glob("*.pkl"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        for model_file in all_models[keep_latest:]:
            model_file.unlink()
            meta_file = model_file.with_suffix('.json')
            if meta_file.exists():
                meta_file.unlink()
            logger.info(f"Removed old model: {model_file.name}")


artifact_manager = ArtifactManager()
