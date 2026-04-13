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
    
    def __init__(self, supply_chain_path: str, fashion_boutique_path: str):
        self.supply_chain_path = Path(supply_chain_path)
        self.fashion_boutique_path = Path(fashion_boutique_path)
        self.supply_chain_df = None
        self.fashion_boutique_df = None
    
    def load_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Load both CSV datasets"""
        try:
            logger.info(f"Loading supply chain data from {self.supply_chain_path}")
            self.supply_chain_df = pd.read_csv(self.supply_chain_path)
            logger.info(f"Loaded {len(self.supply_chain_df)} rows from supply chain data")
            
            logger.info(f"Loading fashion boutique data from {self.fashion_boutique_path}")
            self.fashion_boutique_df = pd.read_csv(self.fashion_boutique_path)
            logger.info(f"Loaded {len(self.fashion_boutique_df)} rows from fashion boutique data")
            
            return self.supply_chain_df, self.fashion_boutique_df
        
        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def validate_data(self) -> bool:
        """Validate the loaded data"""
        if self.supply_chain_df is None or self.fashion_boutique_df is None:
            logger.error("Data not loaded. Call load_data() first.")
            return False
        
        # Check required columns in supply_chain_data
        required_sc_columns = [
            'Product type', 'SKU', 'Price', 'Number of products sold',
            'Revenue generated', 'Stock levels', 'Supplier name', 'Location'
        ]
        
        missing_sc = [col for col in required_sc_columns if col not in self.supply_chain_df.columns]
        if missing_sc:
            logger.error(f"Missing columns in supply chain data: {missing_sc}")
            return False
        
        # Check required columns in fashion_boutique_data
        required_fb_columns = [
            'product_id', 'category', 'brand', 'original_price',
            'current_price', 'stock_quantity'
        ]
        
        missing_fb = [col for col in required_fb_columns if col not in self.fashion_boutique_df.columns]
        if missing_fb:
            logger.error(f"Missing columns in fashion boutique data: {missing_fb}")
            return False
        
        logger.info("Data validation passed")
        return True
    
    def get_data_summary(self) -> dict:
        """Get summary statistics of loaded data"""
        if self.supply_chain_df is None or self.fashion_boutique_df is None:
            return {}
        
        return {
            'supply_chain': {
                'rows': len(self.supply_chain_df),
                'columns': len(self.supply_chain_df.columns),
                'unique_skus': self.supply_chain_df['SKU'].nunique() if 'SKU' in self.supply_chain_df.columns else 0,
                'unique_suppliers': self.supply_chain_df['Supplier name'].nunique() if 'Supplier name' in self.supply_chain_df.columns else 0,
                'unique_locations': self.supply_chain_df['Location'].nunique() if 'Location' in self.supply_chain_df.columns else 0,
            },
            'fashion_boutique': {
                'rows': len(self.fashion_boutique_df),
                'columns': len(self.fashion_boutique_df.columns),
                'unique_products': self.fashion_boutique_df['product_id'].nunique() if 'product_id' in self.fashion_boutique_df.columns else 0,
                'unique_brands': self.fashion_boutique_df['brand'].nunique() if 'brand' in self.fashion_boutique_df.columns else 0,
                'unique_categories': self.fashion_boutique_df['category'].nunique() if 'category' in self.fashion_boutique_df.columns else 0,
            }
        }
