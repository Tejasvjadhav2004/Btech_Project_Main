"""
MongoDB Initializer - Initialize MongoDB with data
"""
from typing import List, Dict, Any
from datetime import datetime
from db.connection import mongodb
import logging

logger = logging.getLogger(__name__)


class MongoInitializer:
    """Initialize MongoDB with data and indexes"""
    
    def __init__(self):
        self.db = mongodb.get_database()
    
    def clear_collections(self):
        """Clear all collections"""
        collections = ['products', 'warehouses', 'stores', 'inventory', 'suppliers', 'orders', 'deliveries']
        for collection_name in collections:
            self.db[collection_name].delete_many({})
            logger.info(f"Cleared collection: {collection_name}")
    
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
            result = self.db.inventory.insert_many(inventory)
            logger.info(f"Inserted {len(result.inserted_ids)} inventory records")
            
            # Create indexes
            self.db.inventory.create_index([("sku", 1), ("location_id", 1)], unique=True)
            self.db.inventory.create_index("location_id")
            self.db.inventory.create_index("sku")
            self.db.inventory.create_index("quantity")
            logger.info("Created indexes for inventory collection")
    
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
        collections = ['products', 'warehouses', 'stores', 'inventory', 'suppliers']
        for collection_name in collections:
            stats[collection_name] = self.db[collection_name].count_documents({})
        return stats
