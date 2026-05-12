"""
MongoDB Initializer - Initialize MongoDB with data
"""
from typing import List, Dict, Any
from datetime import datetime
from db.connection import mongodb
from api.config import settings
import logging
import random

logger = logging.getLogger(__name__)


class MongoInitializer:
    """Initialize MongoDB with data and indexes"""

    def __init__(self):
        self.db = mongodb.get_database()

    def clear_collections(self):
        """Clear all collections including orchestration data"""
        collections = [
            # Core data
            'products', 'warehouses', 'stores', 'inventory', 'suppliers',
            # Orders and deliveries
            'orders', 'deliveries',
            # Locations and transactions
            'locations', 'transactions',
            # Intelligence layer
            'signals', 'event_logs', 'predicted_demand', 'predictive_risks',
            # Orchestration layer
            'replenishment_orders', 'orchestration_history', 'workflows',
            'workflow_logs', 'audit_logs', 'approvals',
            # Execution logs
            'execution_logs'
        ]
        for collection_name in collections:
            result = self.db[collection_name].delete_many({})
            count = result.deleted_count
            logger.info(f"Cleared collection: {collection_name} ({count} documents deleted)")

    def insert_products(self, products: List[Dict[str, Any]]):
        """Insert products into MongoDB"""
        if products:
            result = self.db.products.insert_many(products)
            logger.info(f"Inserted {len(result.inserted_ids)} products")

            # Create indexes
            self.db.products.create_index("sku", unique=True)
            self.db.products.create_index("category")
            self.db.products.create_index("brand")
            logger.info("Created indexes for products collection")

    def insert_warehouses(self, warehouses: List[Dict[str, Any]]):
        """Insert warehouses into MongoDB"""
        if warehouses:
            result = self.db.warehouses.insert_many(warehouses)
            logger.info(f"Inserted {len(result.inserted_ids)} warehouses")

            # Create indexes
            self.db.warehouses.create_index("warehouse_id", unique=True)
            self.db.warehouses.create_index("location.city")
            logger.info("Created indexes for warehouses collection")

    def create_default_warehouses(self) -> List[Dict[str, Any]]:
        """Create default warehouses based on configuration"""
        warehouses = []
        warehouse_cities = getattr(settings, 'warehouse_cities',
                                   ['Mumbai', 'Delhi', 'Bangalore', 'Kolkata', 'Chennai'])

        for i, city in enumerate(warehouse_cities, 1):
            warehouse = {
                'warehouse_id': f'WH00{i}',
                'name': f'{city} Warehouse',
                'location': {
                    'city': city,
                    'state': city,
                    'country': 'India'
                },
                'capacity': 150000,
                'current_utilization': random.randint(30000, 80000),
                'is_active': True,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'efficiency_metrics': {
                    'pick_accuracy': random.uniform(0.95, 0.99),
                    'avg_processing_time': random.uniform(1.5, 3.0)
                }
            }
            warehouses.append(warehouse)

        logger.info(f"Created {len(warehouses)} default warehouses")
        return warehouses

    def create_warehouse_inventory(self, products: List[Dict[str, Any]],
                                    warehouses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create warehouse inventory records for all products"""
        inventory_records = []

        for product in products:
            sku = product.get('sku')
            primary_wh = product.get('primary_warehouse', 'WH001')

            # Create inventory for primary warehouse (high stock)
            for wh in warehouses:
                wh_id = wh.get('warehouse_id')
                is_primary = wh_id == primary_wh

                # Primary warehouse has more stock
                if is_primary:
                    base_qty = random.randint(100, 500)
                    reserved = random.randint(10, 50)
                else:
                    base_qty = random.randint(20, 150)
                    reserved = random.randint(0, 20)

                inventory = {
                    'sku': sku,
                    'location_id': wh_id,
                    'location_type': 'warehouse',

                    # Stock fields
                    'quantity': base_qty,
                    'current_stock': base_qty,
                    'available_stock': base_qty - reserved,
                    'reserved_stock': reserved,
                    'initial_stock': base_qty,
                    'incoming_stock': random.randint(10, 100) if is_primary else random.randint(0, 30),
                    'damaged_stock': random.randint(0, 5),

                    # Thresholds
                    'reorder_threshold': random.randint(20, 50),
                    'reorder_quantity': random.randint(50, 100),
                    'optimal_stock': base_qty * 2,

                    # Status
                    'inventory_status': 'Healthy' if base_qty > 50 else 'Low Stock',

                    # Timestamps
                    'last_updated': datetime.utcnow(),
                    'last_restocked': datetime.utcnow(),
                    'last_restock_date': datetime.utcnow(),

                    # Additional fields
                    'transactions_count': 0,
                    'total_sales': 0,
                    'total_revenue': 0.0,
                    'stock_velocity': 0
                }
                inventory_records.append(inventory)

        logger.info(f"Created {len(inventory_records)} warehouse inventory records")
        return inventory_records
    
    def insert_stores(self, stores: List[Dict[str, Any]]):
        """Insert stores into MongoDB"""
        if stores:
            result = self.db.stores.insert_many(stores)
            logger.info(f"Inserted {len(result.inserted_ids)} stores")
            
            # Create indexes
            self.db.stores.create_index("store_id", unique=True)
            self.db.stores.create_index("location.city")
            logger.info("Created indexes for stores collection")
    
    def insert_suppliers(self, suppliers: List[Dict[str, Any]]):
        """Insert suppliers into MongoDB"""
        if suppliers:
            result = self.db.suppliers.insert_many(suppliers)
            logger.info(f"Inserted {len(result.inserted_ids)} suppliers")
            
            # Create indexes
            self.db.suppliers.create_index("supplier_id", unique=True)
            self.db.suppliers.create_index("name")
            logger.info("Created indexes for suppliers collection")
    
    def insert_inventory(self, inventory: List[Dict[str, Any]]):
        """Insert inventory into MongoDB"""
        if inventory:
            # Remove duplicates by sku + location_id combination
            seen = set()
            unique_inventory = []
            for item in inventory:
                key = (item.get('sku'), item.get('location_id'))
                if key not in seen:
                    seen.add(key)
                    unique_inventory.append(item)
                else:
                    logger.debug(f"Skipping duplicate inventory: sku={item.get('sku')}, location_id={item.get('location_id')}")

            if len(unique_inventory) < len(inventory):
                logger.info(f"Removed {len(inventory) - len(unique_inventory)} duplicate inventory records")

            # Create indexes BEFORE inserting to prevent duplicates at DB level
            self.db.inventory.create_index([("sku", 1), ("location_id", 1)], unique=True)
            self.db.inventory.create_index("location_id")
            self.db.inventory.create_index("sku")
            self.db.inventory.create_index("quantity")

            result = self.db.inventory.insert_many(unique_inventory)
            logger.info(f"Inserted {len(result.inserted_ids)} inventory records")
            logger.info("Created indexes for inventory collection")

    def insert_locations(self, locations: List[Dict[str, Any]]):
        """Insert location data into MongoDB"""
        if locations:
            for location in locations:
                self.db.locations.update_one(
                    {"city": location["city"]},
                    {"$setOnInsert": location},
                    upsert=True
                )

            logger.info(f"Inserted {len(locations)} locations")

            # Create indexes
            self.db.locations.create_index("city", unique=True)
            self.db.locations.create_index([("lat", 1), ("lng", 1)])
            logger.info("Created indexes for locations collection")
    
    def update_warehouse_utilization(self):
        """Update warehouse utilization based on inventory"""
        pipeline = [
            {
                "$match": {"location_type": "warehouse"}
            },
            {
                "$group": {
                    "_id": "$location_id",
                    "total_quantity": {"$sum": "$quantity"}
                }
            }
        ]
        
        results = self.db.inventory.aggregate(pipeline)
        for result in results:
            warehouse_id = result["_id"]
            total_quantity = result["total_quantity"]
            self.db.warehouses.update_one(
                {"warehouse_id": warehouse_id},
                {"$set": {"current_utilization": total_quantity, "updated_at": datetime.utcnow()}}
            )
        
        logger.info("Updated warehouse utilization")
    
    def update_store_utilization(self):
        """Update store utilization based on inventory"""
        pipeline = [
            {
                "$match": {"location_type": "store"}
            },
            {
                "$group": {
                    "_id": "$location_id",
                    "total_quantity": {"$sum": "$quantity"}
                }
            }
        ]
        
        results = self.db.inventory.aggregate(pipeline)
        for result in results:
            store_id = result["_id"]
            total_quantity = result["total_quantity"]
            self.db.stores.update_one(
                {"store_id": store_id},
                {"$set": {"current_utilization": total_quantity, "updated_at": datetime.utcnow()}}
            )
        
        logger.info("Updated store utilization")
    
    def get_collection_stats(self) -> Dict[str, int]:
        """Get statistics for all collections"""
        stats = {}
        collections = ['products', 'warehouses', 'stores', 'inventory', 'suppliers', 'locations', 'transactions']
        for collection_name in collections:
            stats[collection_name] = self.db[collection_name].count_documents({})
        return stats
