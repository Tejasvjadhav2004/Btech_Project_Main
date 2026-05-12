"""
Data Loader - Load and validate CSV datasets
"""
import pandas as pd
from pathlib import Path
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class DataLoader:
    """Load and validate CSV datasets"""
    
    def __init__(self, supply_chain_path: str):
        self.supply_chain_path = Path(supply_chain_path)
        self.supply_chain_df = None
    
    def load_data(self) -> pd.DataFrame:
        """Load CSV dataset"""
        try:
            logger.info(f"Loading supply chain data from {self.supply_chain_path}")
            self.supply_chain_df = pd.read_csv(self.supply_chain_path)
            logger.info(f"Loaded {len(self.supply_chain_df)} rows from supply chain data")
            
            return self.supply_chain_df
        
        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def validate_data(self) -> bool:
        """Validate the loaded data"""
        if self.supply_chain_df is None:
            logger.error("Data not loaded. Call load_data() first.")
            return False
        
        # Check required columns in supply_chain_data
        required_sc_columns = [
            'Product type', 'SKU', 'Price', 'Number of products sold',
            'Revenue generated', 'Stock levels', 'Supplier name', 'Location',
            'City', 'State', 'Country', 'Coordinates_Lat', 'Coordinates_Lng',
            'Primary_Warehouse_ID', 'Secondary_Warehouse_ID', 'Store_Allocations'
        ]
        
        missing_sc = [col for col in required_sc_columns if col not in self.supply_chain_df.columns]
        if missing_sc:
            logger.error(f"Missing columns in supply chain data: {missing_sc}")
            return False
        
        logger.info("Data validation passed")
        return True

    def validate_coordinates(self) -> bool:
        """Validate coordinate data is within India bounds"""
        if self.supply_chain_df is None:
            return False

        # Check India bounds: lat 8-37, lng 68-97
        valid_lat = self.supply_chain_df['Coordinates_Lat'].between(8, 37).all()
        valid_lng = self.supply_chain_df['Coordinates_Lng'].between(68, 97).all()

        if not valid_lat or not valid_lng:
            logger.error("Coordinates outside India bounds")
            return False

        logger.info("Coordinate validation passed")
        return True

    def get_data_summary(self) -> dict:
        """Get summary statistics of loaded data"""
        if self.supply_chain_df is None:
            return {}
        
        return {
            'supply_chain': {
                'rows': len(self.supply_chain_df),
                'columns': len(self.supply_chain_df.columns),
                'unique_skus': self.supply_chain_df['SKU'].nunique() if 'SKU' in self.supply_chain_df.columns else 0,
                'unique_suppliers': self.supply_chain_df['Supplier name'].nunique() if 'Supplier name' in self.supply_chain_df.columns else 0,
                'unique_locations': self.supply_chain_df['Location'].nunique() if 'Location' in self.supply_chain_df.columns else 0,
            }
        }
