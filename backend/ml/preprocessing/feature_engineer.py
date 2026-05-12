"""
Feature Engineer - Creates features for demand forecasting

Generates time-series features including:
- Temporal features (day of week, month, week of year)
- Lag features
- Rolling statistics
- Seasonal indicators
"""
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Creates ML features from processed transaction data"""

    def __init__(self):
        self.feature_columns: List[str] = []

    def create_features(
        self,
        df: pd.DataFrame,
        date_column: str = 'transaction_date',
        target_column: str = 'quantity_sold',
        create_lags: bool = True,
        create_rolling: bool = True,
        create_seasonal: bool = True
    ) -> pd.DataFrame:
        """
        Create all features for demand forecasting.

        Args:
            df: DataFrame with transaction data
            date_column: Name of the date column
            target_column: Name of the target column (for lag features)
            create_lags: Whether to create lag features
            create_rolling: Whether to create rolling statistics
            create_seasonal: Whether to create seasonal features

        Returns:
            DataFrame with new features
        """
        df = df.copy()

        logger.info(f"Creating features for {len(df)} records...")

        # Ensure date column is datetime
        if date_column in df.columns:
            df[date_column] = pd.to_datetime(df[date_column])
        elif 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            date_column = 'date'

        # Create temporal features
        df = self._create_temporal_features(df, date_column)

        # Create lag features
        if create_lags:
            df = self._create_lag_features(df, target_column)

        # Create rolling statistics
        if create_rolling:
            df = self._create_rolling_features(df, target_column)

        # Create seasonal features
        if create_seasonal:
            df = self._create_seasonal_features(df, date_column)

        # Create interaction features
        df = self._create_interaction_features(df)

        # Fill NaN values created by lag/rolling features
        df = df.bfill().ffill().fillna(0)

        # Store feature column names (excluding ID and target columns)
        exclude_cols = [date_column, target_column, 'sku', 'store_id', 'warehouse_id',
                        'product_category', 'supplier_name', 'date']
        self.feature_columns = [col for col in df.columns if col not in exclude_cols]

        logger.info(f"Created {len(self.feature_columns)} features")

        return df

    def _create_temporal_features(self, df: pd.DataFrame, date_column: str) -> pd.DataFrame:
        """Create basic temporal features"""

        dt = df[date_column]

        df['day_of_week'] = dt.dt.dayofweek  # 0=Monday, 6=Sunday
        df['day_of_month'] = dt.dt.day
        df['month'] = dt.dt.month
        df['quarter'] = dt.dt.quarter
        df['week_of_year'] = dt.dt.isocalendar().week.astype(int)
        df['year'] = dt.dt.year
        df['is_weekend'] = (dt.dt.dayofweek >= 5).astype(int)
        df['is_month_start'] = dt.dt.is_month_start.astype(int)
        df['is_month_end'] = dt.dt.is_month_end.astype(int)

        return df

    def _create_lag_features(
        self,
        df: pd.DataFrame,
        target_column: str,
        lags: List[int] = [1, 3, 7, 14, 21, 28]
    ) -> pd.DataFrame:
        """
        Create lag features for time series.

        Args:
            df: DataFrame with sorted data
            target_column: Column to create lags for
            lags: List of lag periods (days)
        """
        if target_column not in df.columns:
            return df

        # Group by SKU-Store for proper lag calculation
        group_cols = []
        for col in ['sku', 'store_id']:
            if col in df.columns:
                group_cols.append(col)

        if not group_cols:
            # No grouping - create simple lags
            for lag in lags:
                df[f'lag_{lag}'] = df[target_column].shift(lag)
        else:
            # Create grouped lags
            for lag in lags:
                df[f'lag_{lag}'] = df.groupby(group_cols)[target_column].shift(lag)

        return df

    def _create_rolling_features(
        self,
        df: pd.DataFrame,
        target_column: str,
        windows: List[int] = [7, 14, 28]
    ) -> pd.DataFrame:
        """
        Create rolling statistics features.

        Calculates mean, std, min, max, median for each window.
        """
        if target_column not in df.columns:
            return df

        # Group by SKU-Store for proper rolling calculation
        group_cols = []
        for col in ['sku', 'store_id']:
            if col in df.columns:
                group_cols.append(col)

        if not group_cols:
            for window in windows:
                df[f'rolling_mean_{window}'] = df[target_column].rolling(window=window).mean()
                df[f'rolling_std_{window}'] = df[target_column].rolling(window=window).std()
                df[f'rolling_min_{window}'] = df[target_column].rolling(window=window).min()
                df[f'rolling_max_{window}'] = df[target_column].rolling(window=window).max()
                df[f'rolling_median_{window}'] = df[target_column].rolling(window=window).median()
                df[f'rolling_sum_{window}'] = df[target_column].rolling(window=window).sum()
        else:
            for window in windows:
                grouped = df.groupby(group_cols)[target_column]
                df[f'rolling_mean_{window}'] = grouped.transform(
                    lambda x: x.rolling(window=window, min_periods=1).mean()
                )
                df[f'rolling_std_{window}'] = grouped.transform(
                    lambda x: x.rolling(window=window, min_periods=1).std()
                )
                df[f'rolling_min_{window}'] = grouped.transform(
                    lambda x: x.rolling(window=window, min_periods=1).min()
                )
                df[f'rolling_max_{window}'] = grouped.transform(
                    lambda x: x.rolling(window=window, min_periods=1).max()
                )
                df[f'rolling_median_{window}'] = grouped.transform(
                    lambda x: x.rolling(window=window, min_periods=1).median()
                )
                df[f'rolling_sum_{window}'] = grouped.transform(
                    lambda x: x.rolling(window=window, min_periods=1).sum()
                )

        # Create rolling trend features
        if 'rolling_mean_7' in df.columns and 'rolling_mean_28' in df.columns:
            df['rolling_trend'] = df['rolling_mean_7'] / df['rolling_mean_28'].replace(0, 1)

        # Create expanding mean feature
        if group_cols:
            df['expanding_mean'] = df.groupby(group_cols)[target_column].transform(
                lambda x: x.expanding(min_periods=1).mean()
            )
        else:
            df['expanding_mean'] = df[target_column].expanding(min_periods=1).mean()

        # Create momentum features (rate of change)
        if 'rolling_mean_7' in df.columns:
            df['momentum_7'] = df.groupby(group_cols)[target_column].transform(
                lambda x: x.diff(7) / x.shift(7).replace(0, 1)
            ) if group_cols else df[target_column].diff(7) / df[target_column].shift(7).replace(0, 1)

        return df

    def _create_seasonal_features(self, df: pd.DataFrame, date_column: str) -> pd.DataFrame:
        """Create seasonal indicator features"""

        dt = df[date_column]

        # Season (winter=0, spring=1, summer=2, fall=3)
        df['season'] = (dt.dt.month % 12 + 3) // 3 - 1

        # Holiday indicators (approximate)
        df['is_holiday_season'] = dt.dt.month.isin([11, 12]).astype(int)

        # Week of month (1-5)
        df['week_of_month'] = (dt.dt.day - 1) // 7 + 1

        # Days until month end
        df['days_until_month_end'] = dt.dt.days_in_month - dt.dt.day

        return df

    def _create_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create interaction features"""

        # Weekend * Month interaction
        if 'is_weekend' in df.columns and 'month' in df.columns:
            df['weekend_month'] = df['is_weekend'] * df['month']

        # Day of week * is_month_end interaction
        if 'day_of_week' in df.columns and 'is_month_end' in df.columns:
            df['dow_month_end'] = df['day_of_week'] * df['is_month_end']

        return df

    def create_future_features(
        self,
        last_date: pd.Timestamp,
        days_ahead: int = 7,
        sku: str = None,
        store_id: str = None,
        historical_stats: Optional[Dict[str, float]] = None,
        required_features: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Create features for future dates (for prediction).

        Args:
            last_date: Last date in historical data
            days_ahead: Number of days to predict ahead
            sku: Product SKU
            store_id: Store ID
            historical_stats: Optional dict with historical statistics
            required_features: List of features that must be present (from trained model)

        Returns:
            DataFrame with features for future dates
        """
        future_dates = pd.date_range(
            start=last_date + pd.Timedelta(days=1),
            periods=days_ahead,
            freq='D'
        )

        future_df = pd.DataFrame({
            'transaction_date': future_dates,
            'sku': sku,
            'store_id': store_id
        })

        # Create temporal features
        future_df = self._create_temporal_features(future_df, 'transaction_date')
        future_df = self._create_seasonal_features(future_df, 'transaction_date')

        # Create interaction features
        future_df = self._create_interaction_features(future_df)

        # Use historical stats for lag/rolling features if available
        default_quantity = 5
        default_std = 1

        if historical_stats:
            default_quantity = historical_stats.get('mean_quantity', 5)
            default_std = historical_stats.get('std_quantity', 1)

        # Set all lag features
        for lag in [1, 3, 7, 14, 21, 28]:
            if historical_stats and f'lag_{lag}' in historical_stats:
                future_df[f'lag_{lag}'] = historical_stats[f'lag_{lag}']
            else:
                future_df[f'lag_{lag}'] = default_quantity

        # Set all rolling features
        for window in [7, 14, 28]:
            if historical_stats:
                future_df[f'rolling_mean_{window}'] = historical_stats.get(f'rolling_mean_{window}', default_quantity)
                future_df[f'rolling_std_{window}'] = historical_stats.get(f'rolling_std_{window}', default_std)
                future_df[f'rolling_min_{window}'] = historical_stats.get(f'rolling_min_{window}', 0)
                future_df[f'rolling_max_{window}'] = historical_stats.get(f'rolling_max_{window}', default_quantity * 2)
                future_df[f'rolling_median_{window}'] = historical_stats.get(f'rolling_median_{window}', default_quantity)
                future_df[f'rolling_sum_{window}'] = historical_stats.get(f'rolling_sum_{window}', default_quantity * window)
            else:
                future_df[f'rolling_mean_{window}'] = default_quantity
                future_df[f'rolling_std_{window}'] = default_std
                future_df[f'rolling_min_{window}'] = 0
                future_df[f'rolling_max_{window}'] = default_quantity * 2
                future_df[f'rolling_median_{window}'] = default_quantity
                future_df[f'rolling_sum_{window}'] = default_quantity * window

        # Rolling trend
        if 'rolling_mean_7' in future_df.columns and 'rolling_mean_28' in future_df.columns:
            future_df['rolling_trend'] = future_df['rolling_mean_7'] / future_df['rolling_mean_28'].replace(0, 1)

        # Expanding mean
        future_df['expanding_mean'] = default_quantity

        # Momentum
        future_df['momentum_7'] = 0

        # Ensure all required features are present (for features we can't compute)
        if required_features:
            for feature in required_features:
                if feature not in future_df.columns:
                    # Set sensible defaults for missing features
                    if 'lag' in feature.lower():
                        future_df[feature] = default_quantity
                    elif 'rolling_mean' in feature.lower() or 'rolling_median' in feature.lower():
                        future_df[feature] = default_quantity
                    elif 'rolling_std' in feature.lower():
                        future_df[feature] = default_std
                    elif 'rolling_min' in feature.lower():
                        future_df[feature] = 0
                    elif 'rolling_max' in feature.lower():
                        future_df[feature] = default_quantity * 2
                    elif 'rolling_sum' in feature.lower():
                        future_df[feature] = default_quantity * 28
                    elif 'trend' in feature.lower() or 'momentum' in feature.lower():
                        future_df[feature] = 0
                    elif 'expanding' in feature.lower():
                        future_df[feature] = default_quantity
                    elif 'encoded' in feature.lower():
                        # Encoded features will be set by the prediction service
                        future_df[feature] = 0
                    else:
                        # Default numerical value for any other missing features
                        future_df[feature] = 0

        # Fill any remaining NaN
        future_df = future_df.fillna(0)

        return future_df

    def get_feature_columns(self) -> List[str]:
        """Get list of feature column names"""
        return self.feature_columns.copy()

    def get_feature_importance_ranking(self) -> List[str]:
        """Get expected feature importance ranking (for documentation)"""
        return [
            'lag_7', 'lag_14', 'rolling_mean_7', 'rolling_mean_14',
            'day_of_week', 'month', 'week_of_year', 'is_weekend',
            'lag_1', 'lag_3', 'season', 'is_holiday_season',
            'rolling_std_7', 'rolling_trend', 'quarter'
        ]


feature_engineer = FeatureEngineer()
