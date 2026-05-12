"""
Data Generator - Generate synthetic data for warehouses and stores using CSV data
"""
from typing import List, Dict, Any
from datetime import datetime
import random
import logging
import pandas as pd

logger = logging.getLogger(__name__)


class DataGenerator:
    """Generate synthetic data for warehouses and stores using CSV data"""

    def __init__(self):
        """Initialize data generator"""
        pass

    def generate_warehouses(self, locations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate warehouse data using real locations from CSV"""
        warehouses = []

        # Map cities to warehouse IDs
        city_warehouse_map = {
            'Mumbai': 'WH001',
            'Delhi': 'WH002',
            'Bangalore': 'WH003',
            'Kolkata': 'WH004',
            'Chennai': 'WH005'
        }

        warehouse_types = ['Central', 'Regional', 'Distribution']

        for location_data in locations:
            city = location_data.get('city')
            
            # Skip if city is missing
            if not city:
                continue
            
            # Only create warehouses for cities in our mapping
            if city not in city_warehouse_map:
                continue

            warehouse_id = city_warehouse_map[city]

            warehouse = {
                'warehouse_id': warehouse_id,
                'name': f"{city} {random.choice(warehouse_types)} Warehouse",
                'location': {
                    'city': city,
                    'state': location_data.get('state', 'Unknown'),
                    'country': location_data.get('country', 'India'),
                    'coordinates': {
                        'lat': location_data.get('lat', 0),
                        'lng': location_data.get('lng', 0)
                    }
                },
                'capacity': random.randint(100000, 300000),  # Increased from 5000-15000 to 100000-300000
                'current_utilization': 0,
                'is_active': True,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'efficiency_metrics': None
            }
            warehouses.append(warehouse)

        logger.info(f"Generated {len(warehouses)} warehouses from CSV locations")
        return warehouses

    def generate_stores(self, locations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate store data using real locations from CSV"""
        stores = []

        # Store city mapping
        store_city_map = {
            'Mumbai': ('ST001', 'Boutique'),
            'Delhi': ('ST002', 'Boutique'),
            'Bangalore': ('ST003', 'Boutique'),
            'Kolkata': ('ST004', 'Boutique'),
            'Chennai': ('ST005', 'Boutique'),
            'Hyderabad': ('ST006', 'Flagship'),
            'Pune': ('ST007', 'Flagship'),
            'Ahmedabad': ('ST008', 'Outlet')
        }

        for location_data in locations:
            city = location_data.get('city')
            
            # Skip if city is missing
            if not city:
                continue
            
            if city not in store_city_map:
                continue

            store_id, store_type = store_city_map[city]

            store = {
                'store_id': store_id,
                'name': f"{city} {store_type} Store",
                'location': {
                    'city': city,
                    'state': location_data.get('state', 'Unknown'),
                    'country': location_data.get('country', 'India'),
                    'coordinates': {
                        'lat': location_data.get('lat', 0),
                        'lng': location_data.get('lng', 0)
                    }
                },
                'store_type': store_type,
                'capacity': random.randint(10000, 30000),  # Increased from 200-800 to 10000-30000
                'current_utilization': 0,
                'is_active': True,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'customer_metrics': None
            }
            stores.append(store)

        logger.info(f"Generated {len(stores)} stores from CSV locations")
        return stores

    def generate_inventory(
        self,
        products: List[Dict],
        warehouses: List[Dict],
        stores: List[Dict],
        supply_chain_df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Generate inventory data using CSV stock levels"""
        inventory = []

        # Create SKU to stock mapping from CSV
        sku_stock_map = {}
        for _, row in supply_chain_df.iterrows():
            sku_stock_map[row['SKU']] = {
                'stock_level': row['Stock levels'],
                'sales': row['Number of products sold'],
                'primary_warehouse': row['Primary_Warehouse_ID'],
                'store_allocations': self._parse_store_allocations(row['Store_Allocations'])
            }

        # Generate inventory for warehouses
        for warehouse in warehouses:
            warehouse_id = warehouse['warehouse_id']

            for product in products:
                sku = product['sku']
                stock_data = sku_stock_map.get(sku, {'stock_level': 100, 'sales': 50, 'primary_warehouse': None, 'store_allocations': {}})

                # Use primary warehouse if specified, otherwise assign to first warehouse (WH001)
                primary_warehouse = stock_data['primary_warehouse']
                if primary_warehouse and primary_warehouse != warehouse_id:
                    continue
                if not primary_warehouse and warehouse_id != 'WH001':
                    continue

                # Use CSV stock level as base
                base_quantity = stock_data['stock_level']
                warehouse_capacity = warehouse['capacity']
                num_products = len(products)
                target_utilization = 0.70

                # Calculate realistic quantity
                quantity = min(
                    base_quantity,
                    int((warehouse_capacity * target_utilization) / num_products)
                )
                quantity = max(10, quantity)

                inv_item = {
                    'sku': sku,
                    'location_id': warehouse_id,
                    'location_type': 'warehouse',
                    
                    # Live tracking fields
                    'current_stock': quantity,
                    'available_stock': quantity,
                    'reserved_stock': 0,
                    'initial_stock': quantity,
                    
                    # Transaction tracking
                    'transactions_count': 0,
                    'total_sales': 0,
                    'total_restock': 0,
                    'last_updated': datetime.utcnow(),
                    
                    # Historical data (for ML)
                    'historical_avg_sales': stock_data['sales'],
                    'historical_patterns': {},
                    
                    # Alert thresholds
                    'reorder_threshold': max(5, quantity // 4),
                    'reorder_quantity': max(10, quantity // 2),
                    
                    # Optimization fields
                    'optimal_stock': quantity,
                    'demand_trend': None,
                    'lead_time_days': None,
                    
                    # Legacy fields for compatibility
                    'quantity': quantity,
                    'last_restocked': datetime.utcnow(),
                    'last_stock_check': datetime.utcnow(),
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow(),
                    'stock_velocity': stock_data['sales']
                }
                inventory.append(inv_item)

        # Ensure all products have at least one inventory record (fallback to WH001)
        product_skus_with_inventory = {inv['sku'] for inv in inventory}
        missing_products = [p for p in products if p['sku'] not in product_skus_with_inventory]
        
        if missing_products:
            logger.warning(f"Found {len(missing_products)} products without inventory, assigning to WH001")
            first_warehouse = warehouses[0] if warehouses else {'warehouse_id': 'WH001', 'capacity': 150000}
            warehouse_id = first_warehouse['warehouse_id']
            
            for product in missing_products:
                sku = product['sku']
                quantity = 50  # Default quantity
                
                inv_item = {
                    'sku': sku,
                    'location_id': warehouse_id,
                    'location_type': 'warehouse',
                    
                    # Live tracking fields
                    'current_stock': quantity,
                    'available_stock': quantity,
                    'reserved_stock': 0,
                    'initial_stock': quantity,
                    
                    # Transaction tracking
                    'transactions_count': 0,
                    'total_sales': 0,
                    'total_restock': 0,
                    'last_updated': datetime.utcnow(),
                    
                    # Historical data (for ML)
                    'historical_avg_sales': 20,
                    'historical_patterns': {},
                    
                    # Alert thresholds
                    'reorder_threshold': 10,
                    'reorder_quantity': 25,
                    
                    # Optimization fields
                    'optimal_stock': quantity,
                    'demand_trend': None,
                    'lead_time_days': None,
                    
                    # Legacy fields for compatibility
                    'quantity': quantity,
                    'last_restocked': datetime.utcnow(),
                    'last_stock_check': datetime.utcnow(),
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow(),
                    'stock_velocity': 20
                }
                inventory.append(inv_item)

        # Generate inventory for stores using allocation percentages
        for store in stores:
            store_id = store['store_id']

            for product in products:
                sku = product['sku']
                stock_data = sku_stock_map.get(sku, {'stock_level': 100, 'sales': 50, 'primary_warehouse': None, 'store_allocations': {}})
                allocations = stock_data.get('store_allocations', {})

                # Check if this store has allocation
                if store_id not in allocations:
                    continue

                # Calculate store quantity based on allocation percentage
                allocation_pct = allocations[store_id]
                warehouse_quantity = stock_data['stock_level']
                store_quantity = int(warehouse_quantity * allocation_pct * 0.5)  # 50% of warehouse stock
                store_quantity = max(5, store_quantity)

                inv_item = {
                    'sku': sku,
                    'location_id': store_id,
                    'location_type': 'store',
                    
                    # Live tracking fields
                    'current_stock': store_quantity,
                    'available_stock': store_quantity,
                    'reserved_stock': 0,
                    'initial_stock': store_quantity,
                    
                    # Transaction tracking
                    'transactions_count': 0,
                    'total_sales': 0,
                    'total_restock': 0,
                    'last_updated': datetime.utcnow(),
                    
                    # Historical data (for ML)
                    'historical_avg_sales': int(stock_data['sales'] * allocation_pct),
                    'historical_patterns': {},
                    
                    # Alert thresholds
                    'reorder_threshold': max(2, store_quantity // 4),
                    'reorder_quantity': max(5, store_quantity // 2),
                    
                    # Optimization fields
                    'optimal_stock': store_quantity,
                    'demand_trend': None,
                    'lead_time_days': None,
                    
                    # Legacy fields for compatibility
                    'quantity': store_quantity,
                    'last_restocked': datetime.utcnow(),
                    'last_stock_check': datetime.utcnow(),
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow(),
                    'stock_velocity': int(stock_data['sales'] * allocation_pct)
                }
                inventory.append(inv_item)

        logger.info(f"Generated {len(inventory)} inventory records from CSV data")
        return inventory

    def _parse_store_allocations(self, allocation_str) -> Dict[str, float]:
        """Parse store allocation string into dictionary"""
        allocations = {}
        if allocation_str and pd.notna(allocation_str):
            for alloc in str(allocation_str).split(';'):
                if ':' in alloc:
                    store_id, percentage = alloc.split(':')
                    allocations[store_id.strip()] = float(percentage.strip())
        return allocations
