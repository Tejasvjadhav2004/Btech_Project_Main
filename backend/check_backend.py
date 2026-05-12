"""
Simple script to check backend server status
"""
import requests
import json

def check_backend():
    """Check if backend is running and inventory endpoint works"""
    print("=" * 60)
    print("CHECKING BACKEND SERVER")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # Check if backend is running
    print("\n1. Checking if backend server is running...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"   ✓ Backend server is running (status: {response.status_code})")
    except requests.exceptions.ConnectionError:
        print("   ✗ Backend server is not running!")
        print("   Hint: Start the backend server with: cd backend && uvicorn api.main:app --reload")
        return
    except Exception as e:
        print(f"   ✗ Error checking backend: {e}")
        return
    
    # Check inventory endpoint
    print("\n2. Checking /api/inventory endpoint...")
    try:
        response = requests.get(f"{base_url}/api/inventory?limit=5")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            inventory_data = response.json()
            print(f"   ✓ Got {len(inventory_data)} inventory records")
            
            if len(inventory_data) > 0:
                print(f"\n   Sample inventory record:")
                print(f"   {json.dumps(inventory_data[0], indent=2, default=str)[:500]}...")
                
                # Check for required fields
                required_fields = ['sku', 'location_id', 'location_type', 'current_stock', 
                                  'available_stock', 'reserved_stock', 'incoming_stock', 
                                  'damaged_stock', 'inventory_status']
                
                print(f"\n   Checking required fields:")
                for field in required_fields:
                    if field in inventory_data[0]:
                        print(f"      ✓ {field}")
                    else:
                        print(f"      ✗ {field} (MISSING)")
            else:
                print("   ✗ No inventory records found")
                print("   Hint: Run seed_data.py to populate the database")
        else:
            print(f"   ✗ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ✗ Error checking inventory endpoint: {e}")
    
    # Check products endpoint
    print("\n3. Checking /api/products endpoint...")
    try:
        response = requests.get(f"{base_url}/api/products?limit=5")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            products_data = response.json()
            print(f"   ✓ Got {len(products_data)} product records")
            
            if len(products_data) > 0:
                print(f"\n   Sample product record:")
                print(f"   {json.dumps(products_data[0], indent=2, default=str)[:500]}...")
            else:
                print("   ✗ No product records found")
        else:
            print(f"   ✗ Error: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Error checking products endpoint: {e}")
    
    print("\n" + "=" * 60)
    print("CHECK COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    check_backend()
