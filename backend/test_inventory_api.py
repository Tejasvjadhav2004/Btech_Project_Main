"""
Test script to verify inventory API and database state
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from db.connection import get_db
from api.models.inventory import InventoryResponse
from api.models.product import ProductResponse
import json

def test_inventory_api():
    """Test inventory API and database state"""
    print("=" * 60)
    print("TESTING INVENTORY API AND DATABASE")
    print("=" * 60)
    
    db = get_db()
    
    # Check if database is connected
    print("\n1. Checking database connection...")
    try:
        db.list_collection_names()
        print("✓ Database connected successfully")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return
    
    # Check collections
    print("\n2. Checking collections...")
    collections = db.list_collection_names()
    print(f"   Collections: {collections}")
    
    # Check inventory collection
    print("\n3. Checking inventory collection...")
    inventory_count = db.inventory.count_documents({})
    print(f"   Total inventory records: {inventory_count}")
    
    if inventory_count == 0:
        print("   ✗ No inventory records found - database is empty!")
        print("   Hint: Run seed_data.py to populate the database")
        return
    
    # Get sample inventory
    print("\n4. Getting sample inventory records...")
    sample_inventory = list(db.inventory.find().limit(3))
    
    for i, inv in enumerate(sample_inventory, 1):
        print(f"\n   --- Inventory Record {i} ---")
        print(f"   SKU: {inv.get('sku')}")
        print(f"   Location: {inv.get('location_id')} ({inv.get('location_type')})")
        print(f"   Current Stock: {inv.get('current_stock')}")
        print(f"   Available Stock: {inv.get('available_stock')}")
        print(f"   Reserved Stock: {inv.get('reserved_stock')}")
        print(f"   Incoming Stock: {inv.get('incoming_stock')}")
        print(f"   Damaged Stock: {inv.get('damaged_stock')}")
        print(f"   Inventory Status: {inv.get('inventory_status')}")
        print(f"   Transactions Count: {inv.get('transactions_count')}")
        print(f"   Total Sales: {inv.get('total_sales')}")
        
        # Check for missing fields
        required_fields = ['sku', 'location_id', 'location_type', 'current_stock', 
                          'available_stock', 'reserved_stock', 'incoming_stock', 
                          'damaged_stock', 'inventory_status']
        missing_fields = [f for f in required_fields if f not in inv or inv[f] is None]
        
        if missing_fields:
            print(f"   ⚠ MISSING FIELDS: {missing_fields}")
        else:
            print(f"   ✓ All required fields present")
    
    # Check products collection
    print("\n5. Checking products collection...")
    products_count = db.products.count_documents({})
    print(f"   Total product records: {products_count}")
    
    if products_count == 0:
        print("   ✗ No product records found")
    else:
        sample_products = list(db.products.find().limit(3))
        for i, prod in enumerate(sample_products, 1):
            print(f"\n   --- Product {i} ---")
            print(f"   SKU: {prod.get('sku')}")
            print(f"   Name: {prod.get('name')}")
            print(f"   Category: {prod.get('category')}")
            print(f"   Current Price: {prod.get('current_price')}")
    
    # Test Pydantic model validation
    print("\n6. Testing Pydantic model validation...")
    if sample_inventory:
        try:
            inv_dict = sample_inventory[0]
            inv_dict["id"] = str(inv_dict["_id"])
            del inv_dict["_id"]
            
            # Try to validate with InventoryResponse
            validated = InventoryResponse(**inv_dict)
            print(f"   ✓ InventoryResponse validation successful")
            print(f"   Validated fields: {validated.model_dump().keys()}")
        except Exception as e:
            print(f"   ✗ Pydantic validation failed: {e}")
            print(f"   First 500 chars of inventory dict: {json.dumps(inv_dict, default=str)[:500]}")
    
    # Check API response structure
    print("\n7. Checking API response structure...")
    print("   Expected InventoryResponse fields:")
    expected_fields = ['id', 'sku', 'location_id', 'location_type', 'current_stock', 
                      'available_stock', 'reserved_stock', 'initial_stock', 'incoming_stock',
                      'damaged_stock', 'inventory_status', 'transactions_count', 'total_sales',
                      'total_restock', 'last_updated', 'historical_avg_sales', 'reorder_threshold',
                      'reorder_quantity', 'optimal_stock', 'demand_trend', 'lead_time_days',
                      'quantity', 'last_restocked', 'last_stock_check', 'created_at', 
                      'updated_at', 'stock_velocity']
    for field in expected_fields:
        print(f"   - {field}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_inventory_api()
