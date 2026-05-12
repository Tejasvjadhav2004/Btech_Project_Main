"""
Run this script to train the initial demand forecast model.

Usage:
    cd backend
    python scripts/train_initial_model.py
"""
import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Change working directory to backend
os.chdir(backend_dir)

from ml.training.train_demand_forecast import DemandForecastTrainer
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Train the demand forecast model"""
    print("=" * 60)
    print("Training Demand Forecast Model")
    print("=" * 60)
    print()

    try:
        trainer = DemandForecastTrainer(model_type="random_forest")

        print("Starting training pipeline...")
        print("  - Loading transaction data")
        print("  - Creating features")
        print("  - Training model")
        print("  - Evaluating performance")
        print()

        results = trainer.train()

        print()
        print("=" * 60)
        print("Training Complete!")
        print("=" * 60)
        print()
        print(f"Model Type: {results['model_type']}")
        print(f"Model Path: {results['model_path']}")
        print(f"Training Time: {results['training_time_seconds']:.2f} seconds")
        print(f"Train Samples: {results['train_samples']}")
        print(f"Test Samples: {results['test_samples']}")
        print(f"Features Used: {results['feature_count']}")
        print()
        print("Evaluation Metrics:")
        print("-" * 40)
        for metric, value in results['metrics'].items():
            print(f"  {metric}: {value:.4f}")
        print()

        if results['feature_importance']:
            print("Top 5 Important Features:")
            print("-" * 40)
            for i, (feature, importance) in enumerate(list(results['feature_importance'].items())[:5]):
                print(f"  {i+1}. {feature}: {importance:.4f}")

        print()
        print("Model saved successfully! You can now:")
        print("  1. Start the backend API")
        print("  2. Generate predictions via /api/predictions/demand/generate")
        print("  3. View predictions in the frontend Predictive AI dashboard")

        return results

    except Exception as e:
        print(f"\nError during training: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()
