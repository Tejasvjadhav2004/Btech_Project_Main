"""
Script to check how location data is stored in the database
"""
from db.connection import get_db
import json

def check_location_data():
    db = get_db()
    
    print("=" * 80)
    print("CHECKING STORES DATA STRUCTURE")
    print("=" * 80)
    
    stores = list(db.stores.find({}))
    print(f"Total stores: {len(stores)}")
    
    if stores:
        print("\nFirst store document structure:")
        first_store = stores[0]
        print(json.dumps(first_store, default=str, indent=2))
        
        print("\n" + "=" * 80)
        print("STORE FIELDS:")
        print("=" * 80)
        for key in sorted(first_store.keys()):
            value = first_store[key]
            print(f"{key}: {value}")
        
        print("\n" + "=" * 80)
        print("CHECKING LOCATION FIELDS:")
        print("=" * 80)
        for field in ['location', 'location_city', 'location_state', 'location_country', 'city', 'state', 'country']:
            if field in first_store:
                print(f"✓ {field}: {first_store[field]}")
            else:
                print(f"✗ {field}: NOT FOUND")
        
        print("\n" + "=" * 80)
        print("ALL STORES LOCATION DATA:")
        print("=" * 80)
        for i, store in enumerate(stores[:5]):  # First 5 stores
            print(f"\nStore {i+1} - ID: {store.get('store_id', 'N/A')}")
            print(f"  Location object: {store.get('location')}")
            print(f"  location_city: {store.get('location_city')}")
            print(f"  location_state: {store.get('location_state')}")
            print(f"  location_country: {store.get('location_country')}")
    
    print("\n\n" + "=" * 80)
    print("CHECKING WAREHOUSES DATA STRUCTURE")
    print("=" * 80)
    
    warehouses = list(db.warehouses.find({}))
    print(f"Total warehouses: {len(warehouses)}")
    
    if warehouses:
        print("\nFirst warehouse document structure:")
        first_warehouse = warehouses[0]
        print(json.dumps(first_warehouse, default=str, indent=2))
        
        print("\n" + "=" * 80)
        print("WAREHOUSE FIELDS:")
        print("=" * 80)
        for key in sorted(first_warehouse.keys()):
            value = first_warehouse[key]
            print(f"{key}: {value}")
        
        print("\n" + "=" * 80)
        print("CHECKING LOCATION FIELDS:")
        print("=" * 80)
        for field in ['location', 'location_city', 'location_state', 'location_country', 'city', 'state', 'country']:
            if field in first_warehouse:
                print(f"✓ {field}: {first_warehouse[field]}")
            else:
                print(f"✗ {field}: NOT FOUND")
        
        print("\n" + "=" * 80)
        print("ALL WAREHOUSES LOCATION DATA:")
        print("=" * 80)
        for i, warehouse in enumerate(warehouses[:5]):  # First 5 warehouses
            print(f"\nWarehouse {i+1} - ID: {warehouse.get('warehouse_id', 'N/A')}")
            print(f"  Location object: {warehouse.get('location')}")
            print(f"  location_city: {warehouse.get('location_city')}")
            print(f"  location_state: {warehouse.get('location_state')}")
            print(f"  location_country: {warehouse.get('location_country')}")

if __name__ == "__main__":
    check_location_data()
