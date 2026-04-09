"""
Data Generator - Generate synthetic data for warehouses and stores
"""
from typing import List, Dict, Any
from datetime import datetime
import random
import logging

logger = logging.getLogger(__name__)


class DataGenerator:
    """Generate synthetic data for warehouses and stores"""
    
    def __init__(self, num_warehouses: int, num_stores: int, warehouse_cities: List[str], store_cities: List[str]):
        self.num_warehouses = num_warehouses
        self.num_stores = num_stores
        self.warehouse_cities = warehouse_cities
        self.store_cities = store_cities
    
    def generate_warehouses(self) -> List[Dict[str, Any]]:
        """Generate warehouse data"""
        warehouses = []
        
        warehouse_types = ['Central', 'Regional', 'Distribution']
        
        for i in range(min(self.num_warehouses, len(self.warehouse_cities))):
            city = self.warehouse_cities[i]
            warehouse_id = f"WH{i+1:03d}"
            
            warehouse = {
                'warehouse_id': warehouse_id,
                'name': f"{city} {random.choice(warehouse_types)} Warehouse",
                'location': {
                    'city': city,
                    'state': None,
                    'country': 'India',
                    'coordinates': {
                        'lat': round(random.uniform(18.0, 28.0), 6),
                        'lng': round(random.uniform(72.0, 88.0), 6)
                    }
                },
                'capacity': random.randint(5000, 15000),
                'current_utilization': 0,
                'is_active': True,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'efficiency_metrics': None
            }
            warehouses.append(warehouse)
        
        logger.info(f"Generated {len(warehouses)} warehouses")
        return warehouses
    
    def generate_stores(self) -> List[Dict[str, Any]]:
        """Generate store data"""
        stores = []
        
        store_types = ['Boutique', 'Flagship', 'Outlet']
        
        for i in range(min(self.num_stores, len(self.store_cities))):
            city = self.store_cities[i]
            store_id = f"ST{i+1:03d}"
            
            store = {
                'store_id': store_id,
                'name': f"{city} {random.choice(store_types)} Store",
                'location': {
                    'city': city,
                    'state': None,
                    'country': 'India',
                    'coordinates': {
                        'lat': round(random.uniform(18.0, 28.0), 6),
                        'lng': round(random.uniform(72.0, 88.0), 6)
                    }
                },
                'store_type': random.choice(store_types),
                'capacity': random.randint(200, 800),
                'current_utilization': 0,
                'is_active': True,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'customer_metrics': None
            }
            stores.append(store)
        
        logger.info(f"Generated {len(stores)} stores")
        return stores
    
    def generate_inventory(self, products: List[Dict], warehouses: List[Dict], stores: List[Dict]) -> List[Dict[str, Any]]:
        """Generate inventory data for products across warehouses and stores"""
        inventory = []
        
        # Generate inventory for warehouses (high stock)
        for product in products:
            for warehouse in warehouses:
                inv_item = {
                    'sku': product['sku'],
                    'location_id': warehouse['warehouse_id'],
                    'location_type': 'warehouse',
                    'quantity': random.randint(100, 500),
                    'reorder_threshold': 20,
                    'reorder_quantity': 50,
                    'last_restocked': datetime.utcnow(),
                    'last_stock_check': datetime.utcnow(),
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow(),
                    'stock_velocity': None,
                    'demand_trend': None,
                    'optimal_stock': None,
                    'lead_time_days': None
                }
                inventory.append(inv_item)
        
        # Generate inventory for stores (low stock)
        for product in products:
            for store in stores:
                inv_item = {
                    'sku': product['sku'],
                    'location_id': store['store_id'],
                    'location_type': 'store',
                    'quantity': random.randint(10, 50),
                    'reorder_threshold': 10,
                    'reorder_quantity': 20,
                    'last_restocked': datetime.utcnow(),
                    'last_stock_check': datetime.utcnow(),
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow(),
                    'stock_velocity': None,
                    'demand_trend': None,
                    'optimal_stock': None,
                    'lead_time_days': None
                }
                inventory.append(inv_item)
        
        logger.info(f"Generated {len(inventory)} inventory records")
        return inventory
