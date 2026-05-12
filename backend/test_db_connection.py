"""Test database connection and data"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from db.connection import mongodb
from api.config import settings

print(f'MongoDB URI: {settings.mongodb_uri}')
print(f'Database: {settings.mongodb_database_name}')

result = mongodb.connect()
print(f'Connected: {result}')

if result:
    db = mongodb.get_database()
    print(f'Collections: {db.list_collection_names()}')
    
    products_count = db.products.count_documents({})
    print(f'Products count: {products_count}')
    
    warehouses_count = db.warehouses.count_documents({})
    print(f'Warehouses count: {warehouses_count}')
    
    stores_count = db.stores.count_documents({})
    print(f'Stores count: {stores_count}')
    
    inventory_count = db.inventory.count_documents({})
    print(f'Inventory count: {inventory_count}')
    
    signals_count = db.signals.count_documents({})
    print(f'Signals count: {signals_count}')
    
    print("\nSample product:")
    product = db.products.find_one()
    if product:
        print(f"  SKU: {product.get('sku')}, Name: {product.get('name')}")
    
    print("\nSample warehouse:")
    warehouse = db.warehouses.find_one()
    if warehouse:
        print(f"  ID: {warehouse.get('warehouse_id')}, Name: {warehouse.get('name')}")
    
    print("\nSample inventory item:")
    inventory = db.inventory.find_one()
    if inventory:
        print(f"  SKU: {inventory.get('sku')}, Location: {inventory.get('location_id')}, Qty: {inventory.get('quantity')}")
