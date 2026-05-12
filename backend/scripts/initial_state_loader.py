"""
Initial State Loader - Load initial inventory state from CSV
"""
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


class InitialStateLoader:
    """Load initial inventory state from CSV"""
    
    def __init__(self, initial_state_path: str, enhanced_data_path: str = None):
        self.initial_state_path = initial_state_path
        self.enhanced_data_path = enhanced_data_path
        self.initial_state_df = None
        self.enhanced_data_df = None
        self.sku_aggregates = {}
    
    def load_initial_state(self) -> pd.DataFrame:
        """Load initial inventory state"""
        try:
            logger.info(f"Loading initial state from {self.initial_state_path}")
            self.initial_state_df = pd.read_csv(self.initial_state_path)
            logger.info(f"Loaded {len(self.initial_state_df)} initial inventory records")
            return self.initial_state_df
        
        except FileNotFoundError as e:
            logger.error(f"Initial state file not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading initial state: {e}")
            raise
    
    def load_enhanced_data(self) -> pd.DataFrame:
        """Load enhanced supply chain dataset"""
        if not self.enhanced_data_path or not os.path.exists(self.enhanced_data_path):
            logger.warning(f"Enhanced data path not found: {self.enhanced_data_path}")
            return None
        
        try:
            logger.info(f"Loading enhanced supply chain data from {self.enhanced_data_path}")
            self.enhanced_data_df = pd.read_csv(self.enhanced_data_path)
            logger.info(f"Loaded {len(self.enhanced_data_df)} enhanced data records")
            return self.enhanced_data_df
        
        except Exception as e:
            logger.error(f"Error loading enhanced data: {e}")
            return None
    
    def aggregate_historical_data(self) -> Dict[str, Dict[str, Any]]:
        """Aggregate transaction data by SKU from enhanced dataset"""
        if self.enhanced_data_df is None:
            logger.warning("Enhanced data not loaded, using zero values")
            return {}
        
        try:
            # Group by SKU and aggregate
            sku_stats = self.enhanced_data_df.groupby('SKU').agg({
                'Number of products sold': ['sum', 'count'],  # total_sales and transactions_count
                'Revenue generated': 'sum'  # total_revenue
            }).reset_index()
            
            # Flatten column names
            sku_stats.columns = ['SKU', 'total_sales', 'transactions_count', 'total_revenue']
            
            # Convert to dictionary
            self.sku_aggregates = {
                row['SKU']: {
                    'transactions_count': int(row['transactions_count']),
                    'total_sales': int(row['total_sales']),
                    'total_revenue': float(row['total_revenue'])
                }
                for _, row in sku_stats.iterrows()
            }
            
            logger.info(f"Aggregated historical data for {len(self.sku_aggregates)} SKUs")
            return self.sku_aggregates
        
        except Exception as e:
            logger.error(f"Error aggregating historical data: {e}")
            return {}
    
    def validate_initial_state(self) -> bool:
        """Validate initial state data"""
        if self.initial_state_df is None:
            logger.error("Initial state not loaded")
            return False
        
        required_columns = [
            'sku', 'location_id', 'location_type',
            'current_stock', 'available_stock', 'reserved_stock'
        ]
        
        missing = [col for col in required_columns if col not in self.initial_state_df.columns]
        if missing:
            logger.error(f"Missing columns: {missing}")
            return False
        
        logger.info("Initial state validation passed")
        return True
    
    def get_initial_inventory_records(self) -> List[Dict[str, Any]]:
        """Get initial inventory records"""
        if self.initial_state_df is None:
            logger.error("Initial state not loaded")
            return []
        
        # Load and aggregate historical data if not already done
        if not self.sku_aggregates and self.enhanced_data_path:
            self.load_enhanced_data()
            self.aggregate_historical_data()
        
        records = []
        for _, row in self.initial_state_df.iterrows():
            sku = row['sku']
            
            # Get historical data for this SKU if available
            sku_data = self.sku_aggregates.get(sku, {
                'transactions_count': 0,
                'total_sales': 0,
                'total_revenue': 0
            })
            
            record = {
                'sku': sku,
                'location_id': row['location_id'],
                'location_type': row['location_type'],
                
                # Live tracking fields
                'current_stock': int(row['current_stock']),
                'available_stock': int(row['available_stock']),
                'reserved_stock': int(row['reserved_stock']),
                'initial_stock': int(row['current_stock']),
                
                # Additional stock tracking
                'incoming_stock': int(row.get('incoming_stock', 0)),
                'damaged_stock': int(row.get('damaged_stock', 0)),
                
                # Transaction tracking (from enhanced dataset)
                'transactions_count': sku_data['transactions_count'],
                'total_sales': sku_data['total_sales'],
                'total_revenue': sku_data['total_revenue'],
                'total_restock': 0,
                'last_updated': datetime.utcnow(),
                
                # Historical data (from CSV if available)
                'historical_avg_sales': sku_data['total_sales'] if sku_data['transactions_count'] > 0 else int(row.get('historical_sales', 0)),
                'historical_patterns': {},
                
                # Alert thresholds
                'reorder_threshold': int(row.get('reorder_threshold', max(5, int(row['current_stock']) // 4))),
                'reorder_quantity': int(row.get('reorder_quantity', max(10, int(row['current_stock']) // 2))),
                
                # Optimization fields
                'optimal_stock': int(row['current_stock']),
                'demand_trend': None,
                'lead_time_days': None,
                
                # Legacy fields
                'quantity': int(row['current_stock']),
                'last_restocked': datetime.utcnow(),
                'stock_velocity': 0,
                
                # Inventory status
                'inventory_status': row.get('inventory_status', 'Healthy'),
                'last_restock_date': datetime.utcnow()
            }
            records.append(record)
        
        logger.info(f"Converted {len(records)} inventory records with historical data")
        return records
    
    def get_warehouses_from_csv(self) -> List[Dict[str, Any]]:
        """Get warehouse information from CSV"""
        if self.initial_state_df is None:
            logger.error("Initial state not loaded")
            return []
        
        warehouses = {}
        
        # Get unique warehouse records
        warehouse_records = self.initial_state_df[
            self.initial_state_df['location_type'] == 'warehouse'
        ]
        
        for _, row in warehouse_records.iterrows():
            location_id = row['location_id']
            
            if location_id not in warehouses:
                warehouses[location_id] = {
                    'warehouse_id': location_id,
                    'name': f"{row.get('location_city', 'Unknown')} Warehouse",
                    'location': {
                        'city': row.get('location_city', 'Unknown'),
                        'state': 'Unknown',
                        'country': 'India'
                    },
                    'capacity': int(row.get('warehouse_capacity', 150000)),
                    'current_utilization': 0,
                    'is_active': True,
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow(),
                    'efficiency_metrics': None
                }
        
        logger.info(f"Extracted {len(warehouses)} warehouses from CSV")
        return list(warehouses.values())
    
    def get_stores_from_csv(self) -> List[Dict[str, Any]]:
        """Get store information from CSV"""
        if self.initial_state_df is None:
            logger.error("Initial state not loaded")
            return []
        
        stores = {}
        
        # Get unique store records
        store_records = self.initial_state_df[
            self.initial_state_df['location_type'] == 'store'
        ]
        
        for _, row in store_records.iterrows():
            location_id = row['location_id']
            
            if location_id not in stores:
                stores[location_id] = {
                    'store_id': location_id,
                    'name': f"{row.get('location_city', 'Unknown')} Store",
                    'location': {
                        'city': row.get('location_city', 'Unknown'),
                        'state': 'Unknown',
                        'country': 'India'
                    },
                    'capacity': int(row.get('store_capacity', 15000)),
                    'current_utilization': 0,
                    'is_active': True,
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow(),
                    'efficiency_metrics': None
                }
        
        logger.info(f"Extracted {len(stores)} stores from CSV")
        return list(stores.values())
    
    def get_products_from_csv(self) -> List[Dict[str, Any]]:
        """Get product information from CSV"""
        if self.initial_state_df is None:
            logger.error("Initial state not loaded")
            return []
        
        products = {}
        
        for _, row in self.initial_state_df.iterrows():
            sku = row['sku']
            
            if sku not in products:
                products[sku] = {
                    'sku': sku,
                    'name': f"{row.get('product_category', 'Product')} {sku}",
                    'category': row.get('product_category', 'other'),
                    'brand': row.get('supplier_name', 'Unknown'),
                    'product_type': row.get('product_category', 'other'),
                    'original_price': float(row.get('product_price', 0)),
                    'current_price': float(row.get('product_price', 0)),
                    'average_rating': None,
                    'total_sales': 0,
                    'total_revenue': 0.0,
                    'is_active': True,
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow(),
                    'location': {
                        'city': 'Unknown',
                        'state': 'Unknown',
                        'country': 'India'
                    },
                    'primary_warehouse': row.get('primary_warehouse_id'),
                    'secondary_warehouse': row.get('secondary_warehouse_id'),
                    'store_allocations': {},
                    'demand_forecast': None,
                    'optimization_score': None,
                    'tags': [row.get('product_category', 'other')]
                }
        
        logger.info(f"Extracted {len(products)} unique products from CSV")
        return list(products.values())
    
    def get_data_summary(self) -> dict:
        """Get summary statistics"""
        if self.initial_state_df is None:
            return {}
        
        return {
            'total_records': len(self.initial_state_df),
            'unique_skus': self.initial_state_df['sku'].nunique(),
            'unique_locations': self.initial_state_df['location_id'].nunique(),
            'warehouses': len(self.initial_state_df[self.initial_state_df['location_type'] == 'warehouse']),
            'stores': len(self.initial_state_df[self.initial_state_df['location_type'] == 'store']),
            'categories': self.initial_state_df['product_category'].nunique() if 'product_category' in self.initial_state_df.columns else 0
        }
