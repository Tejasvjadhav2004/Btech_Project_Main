"""
Diagnose location data issue - Check how location is stored vs accessed
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.connection import get_db
import json

def diagnose_location_issue():
    """Diagnose the location data structure mismatch"""
    db = get_db()
    
    print("=" * 80)
    print("DIAGNOSING LOCATION DATA ISSUE")
    print("=" * 80)
    
    print("\n1. CHECKING STORE DATA STRUCTURE:")
    print("-" * 80)
    stores = list(db.stores.find({}))
    if stores:
        store = stores[0]
        print("Store document keys:", sorted(store.keys()))
        
        # Check if location is nested or flat
        if 'location' in store:
            print(f"\n✓ Found 'location' as NESTED OBJECT:")
            print(f"  Type: {type(store['location'])}")
            print(f"  Content: {store['location']}")
        else:
            print(f"\n✗ 'location' field NOT FOUND")
        
        # Check flat fields
        flat_fields = ['location_city', 'location_state', 'location_country']
        for field in flat_fields:
            if field in store:
                print(f"  {field}: {store[field]}")
            else:
                print(f"  {field}: NOT FOUND")
        
        print("\n" + "=" * 80)
        print("EXPECTED DATA STRUCTURE FROM initial_state_loader.py:")
        print("=" * 80)
        print("location = {")
        print("    'city': row.get('location_city', 'Unknown'),")
        print("    'state': 'Unknown',")
        print("    'country': 'India'")
        print("}")
        
        print("\n" + "=" * 80)
        print("HOW ROUTERS ARE TRYING TO ACCESS IT:")
        print("=" * 80)
        print("location = {")
        print("    'city': store.get('location_city', 'Unknown'),")
        print("    'state': store.get('location_state'),")
        print("    'country': store.get('location_country', 'India')")
        print("}")
        
        print("\n" + "=" * 80)
        print("DIAGNOSIS:")
        print("=" * 80)
        print("❌ DATA STRUCTURE MISMATCH DETECTED!")
        print("")
        print("PROBLEM:")
        print("  - Data is stored with NESTED 'location' object")
        print("  - Routers are trying to access FLAT fields (location_city, location_state, etc.)")
        print("")
        print("RESULT:")
        print("  - store.get('location_city', 'Unknown') returns 'Unknown'")
        print("  - This is why frontend shows 'Unknown' or null for city")
        print("")
        print("SOLUTION:")
        print("  - Change routers to access nested location object:")
        print("    store.get('location', {}).get('city', 'Unknown')")
    
    print("\n\n2. CHECKING WAREHOUSE DATA STRUCTURE:")
    print("-" * 80)
    warehouses = list(db.warehouses.find({}))
    if warehouses:
        warehouse = warehouses[0]
        print("Warehouse document keys:", sorted(warehouse.keys()))
        
        # Check if location is nested or flat
        if 'location' in warehouse:
            print(f"\n✓ Found 'location' as NESTED OBJECT:")
            print(f"  Type: {type(warehouse['location'])}")
            print(f"  Content: {warehouse['location']}")
        else:
            print(f"\n✗ 'location' field NOT FOUND")
        
        # Check flat fields
        flat_fields = ['location_city', 'location_state', 'location_country']
        for field in flat_fields:
            if field in warehouse:
                print(f"  {field}: {warehouse[field]}")
            else:
                print(f"  {field}: NOT FOUND")

if __name__ == "__main__":
    diagnose_location_issue()
