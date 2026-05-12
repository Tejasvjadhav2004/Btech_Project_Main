"""Test MongoDB connection and verify data"""
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

print(f"MONGODB_URI from env: {os.environ.get('MONGODB_URI')}")
print(f"MONGO_DB_NAME from env: {os.environ.get('MONGO_DB_NAME')}")

from db.connection import mongodb
from api.config import settings

print(f"\nSettings MongoDB URI: {settings.mongodb_uri}")
print(f"Settings DB Name: {settings.mongodb_database_name}")

# Connect
print("\nConnecting to MongoDB...")
result = mongodb.connect()
print(f"Connection result: {result}")

if result:
    db = mongodb.get_database()
    print(f"\nDatabase name: {db.name}")
    print(f"Collections: {db.list_collection_names()}")
    
    # Check counts
    products_count = db.products.count_documents({})
    print(f"\nProducts count: {products_count}")
    
    warehouses_count = db.warehouses.count_documents({})
    print(f"Warehouses count: {warehouses_count}")
    
    stores_count = db.stores.count_documents({})
    print(f"Stores count: {stores_count}")
    
    inventory_count = db.inventory.count_documents({})
    print(f"Inventory count: {inventory_count}")
    
    signals_count = db.signals.count_documents({})
    print(f"Signals count: {signals_count}")
    
    # Sample data
    print("\n=== Sample Data ===")
    product = db.products.find_one()
    if product:
        print(f"Product: SKU={product.get('sku')}, Name={product.get('name')}")
    else:
        print("No products found!")
    
    warehouse = db.warehouses.find_one()
    if warehouse:
        print(f"Warehouse: ID={warehouse.get('warehouse_id')}, Name={warehouse.get('name')}")
    else:
        print("No warehouses found!")
    
    inventory_item = db.inventory.find_one()
    if inventory_item:
        print(f"Inventory: SKU={inventory_item.get('sku')}, Location={inventory_item.get('location_id')}, Qty={inventory_item.get('quantity')}")
    else:
        print("No inventory found!")
