"""
Data Processor - Handles data loading and initial processing

Processes raw transaction data for demand forecasting.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataProcessor:
    """Processes raw supply chain transaction data for ML training"""

    DEFAULT_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "raw" / "synthetic_supply_chain_transactions.csv"

    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path or self.DEFAULT_DATA_PATH
        self.raw_data: Optional[pd.DataFrame] = None
        self.processed_data: Optional[pd.DataFrame] = None

    def load_data(self) -> pd.DataFrame:
        """Load raw transaction data from CSV"""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_path}")

        logger.info(f"Loading data from {self.data_path}")
        self.raw_data = pd.read_csv(self.data_path)

        logger.info(f"Loaded {len(self.raw_data)} transactions")
        return self.raw_data

    def preprocess(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Preprocess the raw transaction data.

        Steps:
        1. Parse dates
        2. Sort by date
        3. Handle missing values
        4. Encode categorical variables
        5. Create base features

        Args:
            df: Optional DataFrame to process (uses loaded data if None)

        Returns:
            Preprocessed DataFrame
        """
        if df is None:
            df = self.raw_data if self.raw_data is not None else self.load_data()

        logger.info("Starting data preprocessing...")

        # Make a copy to avoid modifying original
        df = df.copy()

        # Convert transaction_date to datetime
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])

        # Sort by date
        df = df.sort_values('transaction_date').reset_index(drop=True)

        # Handle missing values
        df['quantity_sold'] = df['quantity_sold'].fillna(0)
        df['unit_price'] = df['unit_price'].fillna(df['unit_price'].median())
        df['total_sales'] = df['total_sales'].fillna(df['quantity_sold'] * df['unit_price'])

        # Convert delivery dates if present
        if 'expected_delivery_date' in df.columns:
            df['expected_delivery_date'] = pd.to_datetime(df['expected_delivery_date'], errors='coerce')
        if 'actual_delivery_date' in df.columns:
            df['actual_delivery_date'] = pd.to_datetime(df['actual_delivery_date'], errors='coerce')

        # Create delivery delay feature
        if 'expected_delivery_date' in df.columns and 'actual_delivery_date' in df.columns:
            df['delivery_delay_days'] = (
                df['actual_delivery_date'] - df['expected_delivery_date']
            ).dt.days
            df['delivery_delay_days'] = df['delivery_delay_days'].fillna(0)

        # Create is_delayed binary feature
        if 'delivery_status' in df.columns:
            df['is_delayed'] = (df['delivery_status'] == 'delayed').astype(int)

        # Encode delivery_status categorical
        if 'delivery_status' in df.columns:
            df['delivery_status_encoded'] = df['delivery_status'].map({
                'on_time': 0,
                'delayed': 1,
                'early': -1
            }).fillna(0)

        self.processed_data = df
        logger.info(f"Preprocessed {len(df)} records")

        return df

    def aggregate_by_sku_store_date(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Aggregate transaction data by SKU, Store, and Date.

        This creates a daily time series for each SKU-Store combination.

        Args:
            df: Optional DataFrame to aggregate (uses processed data if None)

        Returns:
            Aggregated DataFrame with daily demand per SKU-Store
        """
        if df is None:
            df = self.processed_data if self.processed_data is not None else self.preprocess()

        logger.info("Aggregating data by SKU, Store, and Date...")

        agg_df = df.groupby(['sku', 'store_id', 'warehouse_id', 'transaction_date']).agg({
            'quantity_sold': 'sum',
            'total_sales': 'sum',
            'unit_price': 'mean',
            'product_category': 'first',
            'reorder_threshold': 'first',
            'supplier_name': 'first',
            'is_delayed': 'mean'  # Proportion of delayed deliveries
        }).reset_index()

        agg_df.columns = ['sku', 'store_id', 'warehouse_id', 'date',
                          'quantity_sold', 'total_sales', 'avg_unit_price',
                          'product_category', 'reorder_threshold', 'supplier_name', 'delay_rate']

        logger.info(f"Aggregated to {len(agg_df)} records")

        return agg_df

    def get_sku_store_combinations(self, df: Optional[pd.DataFrame] = None) -> List[Dict[str, str]]:
        """
        Get unique SKU-Store combinations from the data.

        Returns:
            List of dicts with 'sku' and 'store_id' keys
        """
        if df is None:
            df = self.processed_data if self.processed_data is not None else self.preprocess()

        combinations = df[['sku', 'store_id']].drop_duplicates().to_dict('records')
        return combinations

    def get_data_for_sku_store(
        self,
        sku: str,
        store_id: str,
        df: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Get time series data for a specific SKU-Store combination.

        Args:
            sku: Product SKU
            store_id: Store ID
            df: Optional DataFrame to filter (uses processed data if None)

        Returns:
            Filtered DataFrame for the SKU-Store
        """
        if df is None:
            df = self.processed_data if self.processed_data is not None else self.preprocess()

        mask = (df['sku'] == sku) & (df['store_id'] == store_id)
        filtered_df = df[mask].copy()

        return filtered_df.sort_values('transaction_date').reset_index(drop=True)

    def split_train_test(
        self,
        df: pd.DataFrame,
        test_size: float = 0.2,
        date_column: str = 'transaction_date'
    ) -> tuple:
        """
        Split data into training and test sets based on time.

        Uses a time-based split to avoid data leakage.

        Args:
            df: DataFrame to split
            test_size: Proportion of data for testing (0.0 to 1.0)
            date_column: Column to use for time-based splitting

        Returns:
            Tuple of (train_df, test_df)
        """
        if date_column not in df.columns:
            date_column = 'date'

        df = df.sort_values(date_column).reset_index(drop=True)

        split_idx = int(len(df) * (1 - test_size))
        train_df = df.iloc[:split_idx].copy()
        test_df = df.iloc[split_idx:].copy()

        logger.info(f"Train set: {len(train_df)} records, Test set: {len(test_df)} records")

        return train_df, test_df

    def get_data_summary(self, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Get summary statistics of the data"""
        if df is None:
            df = self.processed_data if self.processed_data is not None else self.preprocess()

        summary = {
            "total_records": len(df),
            "unique_skus": df['sku'].nunique() if 'sku' in df.columns else 0,
            "unique_stores": df['store_id'].nunique() if 'store_id' in df.columns else 0,
            "unique_warehouses": df['warehouse_id'].nunique() if 'warehouse_id' in df.columns else 0,
            "date_range": {
                "start": str(df['transaction_date'].min()) if 'transaction_date' in df.columns else None,
                "end": str(df['transaction_date'].max()) if 'transaction_date' in df.columns else None
            },
            "total_quantity_sold": int(df['quantity_sold'].sum()) if 'quantity_sold' in df.columns else 0,
            "avg_daily_quantity": float(df['quantity_sold'].mean()) if 'quantity_sold' in df.columns else 0,
            "delay_rate": float(df['is_delayed'].mean()) if 'is_delayed' in df.columns else 0
        }

        return summary


data_processor = DataProcessor()
