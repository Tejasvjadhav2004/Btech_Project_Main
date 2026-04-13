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
        
        # Generate inventory for warehouses (proportional to capacity)
        for warehouse in warehouses:
            # Calculate per-product capacity to maintain 60-90% utilization
            warehouse_capacity = warehouse['capacity']
            num_products = len(products)
            
            # Target utilization: 70% average (range: 60-90%)
            target_utilization = 0.70
            utilization_variance = 0.15  # ±15% variance
            
            # Calculate base quantity per product
            base_per_product = int((warehouse_capacity * target_utilization) / num_products)
            
            # Calculate min/max with variance
            min_per_product = int(base_per_product * (1 - utilization_variance))
            max_per_product = int(base_per_product * (1 + utilization_variance))
            
            # Ensure minimum of 10 units per product
            min_per_product = max(10, min_per_product)
            max_per_product = max(20, max_per_product)
            
            for product in products:
                inv_item = {
                    'sku': product['sku'],
                    'location_id': warehouse['warehouse_id'],
                    'location_type': 'warehouse',
                    'quantity': random.randint(min_per_product, max_per_product),
                    'reorder_threshold': max(5, min_per_product // 4),
                    'reorder_quantity': max(10, min_per_product // 2),
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
        
        # Generate inventory for stores (proportional to capacity)
        for store in stores:
            # Calculate per-product capacity for stores
            store_capacity = store['capacity']
            num_products = len(products)
            
            # Target utilization: 50% average (range: 40-60%)
            target_utilization = 0.50
            utilization_variance = 0.10  # ±10% variance
            
            # Calculate base quantity per product
            base_per_product = int((store_capacity * target_utilization) / num_products)
            
            # Calculate min/max with variance
            min_per_product = int(base_per_product * (1 - utilization_variance))
            max_per_product = int(base_per_product * (1 + utilization_variance))
            
            # Ensure minimum of 5 units per product
            min_per_product = max(5, min_per_product)
            max_per_product = max(10, max_per_product)
            
            for product in products:
                inv_item = {
                    'sku': product['sku'],
                    'location_id': store['store_id'],
                    'location_type': 'store',
                    'quantity': random.randint(min_per_product, max_per_product),
                    'reorder_threshold': max(2, min_per_product // 4),
                    'reorder_quantity': max(5, min_per_product // 2),
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
