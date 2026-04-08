"""
Example Scenario Script - Demonstrates Complete Order Execution Flow

This script demonstrates the Phase 2 Order Execution & Decision System by:
1. Creating an order for a store
2. Processing the order (warehouse selection, inventory allocation, delivery creation)
3. Shipping and delivering the order
4. Showing before/after inventory states

Run this script after starting the API server:
    python -m api.main
    python scripts/example_scenario.py
"""

import requests
import json
import time
from datetime import datetime

API_BASE_URL = "http://localhost:8000"


def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_step(step_num: int, description: str):
    """Print a step indicator"""
    print(f"\n{'─' * 40}")
    print(f"📌 Step {step_num}: {description}")
    print("─" * 40)


def print_json(data: dict, indent: int = 2):
    """Pretty print JSON data"""
    print(json.dumps(data, indent=indent, default=str))


def check_api_health():
    """Check if API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API is healthy")
            return True
        print("❌ API health check failed")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure the server is running:")
        print("   python -m api.main")
        return False


def get_sample_product():
    """Get a sample product SKU from the database"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/products?limit=5")
        if response.status_code == 200:
            products = response.json()
            if products:
                return products[0]
        return None
    except Exception as e:
        print(f"Error fetching products: {e}")
        return None


def get_sample_store():
    """Get a sample store from the database"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/stores")
        if response.status_code == 200:
            stores = response.json()
            if stores:
                return stores[0]
        return None
    except Exception as e:
        print(f"Error fetching stores: {e}")
        return None


def get_inventory_status(sku: str, location_type: str = "warehouse"):
    """Get current inventory status for a SKU"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/inventory",
            params={"sku": sku, "location_type": location_type}
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"Error fetching inventory: {e}")
        return []


def create_order(sku: str, quantity: int, store_id: str, priority: str = "normal"):
    """Create a new order"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/orders/create",
            json={
                "sku": sku,
                "quantity": quantity,
                "store_id": store_id,
                "priority": priority
            }
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.json().get('detail', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"Error creating order: {e}")
        return None


def process_order(order_id: str):
    """Process an order through the execution pipeline"""
    try:
        response = requests.post(f"{API_BASE_URL}/api/orders/process/{order_id}")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.json().get('detail', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"Error processing order: {e}")
        return None


def ship_order(order_id: str):
    """Ship an order"""
    try:
        response = requests.post(f"{API_BASE_URL}/api/orders/{order_id}/ship")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.json().get('detail', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"Error shipping order: {e}")
        return None


def deliver_order(order_id: str):
    """Mark order as delivered"""
    try:
        response = requests.post(f"{API_BASE_URL}/api/orders/{order_id}/deliver")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.json().get('detail', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"Error delivering order: {e}")
        return None


def get_order(order_id: str):
    """Get order details"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/orders/{order_id}")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error fetching order: {e}")
        return None


def run_example_scenario():
    """Run the complete example scenario"""
    
    print_header("SUPPLY CHAIN ORDER EXECUTION - EXAMPLE SCENARIO")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Check API health
    print_step(0, "Checking API Health")
    if not check_api_health():
        return
    
    # Get sample data
    print_step(1, "Fetching Sample Data")
    
    product = get_sample_product()
    if not product:
        print("❌ No products found in database. Please load sample data first.")
        return
    
    store = get_sample_store()
    if not store:
        print("❌ No stores found in database. Please load sample data first.")
        return
    
    sku = product.get("sku")
    store_id = store.get("store_id")
    quantity = 10
    
    print(f"\n📦 Selected Product: {product.get('name', sku)}")
    print(f"   SKU: {sku}")
    print(f"   Price: ${product.get('price', 0):.2f}")
    
    print(f"\n🏪 Selected Store: {store.get('name', store_id)}")
    print(f"   Store ID: {store_id}")
    print(f"   City: {store.get('location', {}).get('city', 'Unknown')}")
    
    print(f"\n📝 Order Details:")
    print(f"   Quantity: {quantity}")
    print(f"   Priority: normal")
    
    # Get initial inventory state
    print_step(2, "Checking Initial Inventory State")
    
    initial_inventory = get_inventory_status(sku)
    print("\n📊 Warehouse Inventory BEFORE Order:")
    for inv in initial_inventory[:5]:  # Show top 5
        available = inv.get('quantity', 0) - inv.get('reserved_stock', 0)
        print(f"   {inv.get('location_id')}: {inv.get('quantity', 0)} total, "
              f"{inv.get('reserved_stock', 0)} reserved, {available} available")
    
    # Create order
    print_step(3, "Creating Order")
    
    order_result = create_order(sku, quantity, store_id, "normal")
    if not order_result:
        print("❌ Failed to create order")
        return
    
    order = order_result.get("order", {})
    order_id = order.get("order_id")
    
    print(f"\n✅ Order Created Successfully!")
    print(f"   Order ID: {order_id}")
    print(f"   Status: {order.get('status')}")
    print(f"   Total Amount: ${order.get('total_amount', 0):.2f}")
    print(f"   Priority: {order.get('priority')}")
    
    # Process order (the magic happens here!)
    print_step(4, "Processing Order (Execution Pipeline)")
    print("\nExecuting pipeline:")
    print("   1. Validating order...")
    print("   2. Selecting optimal warehouse...")
    print("   3. Allocating inventory...")
    print("   4. Creating delivery...")
    print("   5. Updating order status...")
    
    process_result = process_order(order_id)
    if not process_result:
        print("❌ Failed to process order")
        return
    
    print("\n✅ Order Processed Successfully!")
    
    # Show execution details
    execution_id = process_result.get("execution_id")
    warehouse_decision = process_result.get("warehouse_decision", {})
    allocation = process_result.get("allocation", {})
    delivery = process_result.get("delivery", {})
    
    print(f"\n📋 Execution ID: {execution_id}")
    
    # Warehouse selection details
    selected_wh = warehouse_decision.get("selected_warehouse", {})
    print(f"\n🏭 Warehouse Selection Decision:")
    print(f"   Selected: {selected_wh.get('warehouse_id')}")
    print(f"   City: {selected_wh.get('city')}")
    print(f"   Distance: {selected_wh.get('distance_km', 0):.2f} km")
    print(f"   Available Stock: {selected_wh.get('available_stock')}")
    print(f"   Utilization: {selected_wh.get('utilization_percent', 0):.1f}%")
    
    # Show alternatives considered
    alternatives = warehouse_decision.get("alternatives", [])
    if alternatives:
        print(f"\n   📍 Alternative Warehouses Considered:")
        for alt in alternatives[:3]:
            print(f"      - {alt.get('warehouse_id')}: {alt.get('distance_km', 0):.2f}km, "
                  f"{alt.get('available_stock')} units available")
    
    # Inventory allocation details
    print(f"\n📦 Inventory Allocation:")
    print(f"   Warehouse: {allocation.get('warehouse_id')}")
    print(f"   Quantity Allocated: {allocation.get('quantity_allocated')}")
    print(f"   Before: {allocation.get('before', {}).get('available_stock')} available")
    print(f"   After: {allocation.get('after', {}).get('available_stock')} available")
    
    # Delivery details
    print(f"\n🚚 Delivery Created:")
    print(f"   Delivery ID: {delivery.get('delivery_id')}")
    print(f"   Route: {delivery.get('warehouse_id')} → {delivery.get('store_id')}")
    print(f"   Distance: {delivery.get('distance_km', 0):.2f} km")
    print(f"   Transport Mode: {delivery.get('transport_mode')}")
    print(f"   Estimated Time: {delivery.get('estimated_duration_hours', 0):.1f} hours")
    print(f"   Carrier: {delivery.get('carrier')}")
    
    # Get updated order
    updated_order = get_order(order_id)
    print(f"\n📄 Updated Order Status: {updated_order.get('status')}")
    print(f"   Assigned Warehouse: {updated_order.get('assigned_warehouse')}")
    print(f"   Delivery ID: {updated_order.get('delivery_id')}")
    
    # Ship order
    print_step(5, "Shipping Order")
    
    ship_result = ship_order(order_id)
    if ship_result:
        print(f"✅ Order Shipped!")
        print(f"   Status: {ship_result.get('order', {}).get('status')}")
    
    # Check inventory after shipment
    print_step(6, "Checking Inventory After Shipment")
    
    final_inventory = get_inventory_status(sku)
    print("\n📊 Warehouse Inventory AFTER Shipment:")
    for inv in final_inventory[:5]:
        available = inv.get('quantity', 0) - inv.get('reserved_stock', 0)
        print(f"   {inv.get('location_id')}: {inv.get('quantity', 0)} total, "
              f"{inv.get('reserved_stock', 0)} reserved, {available} available")
    
    # Deliver order
    print_step(7, "Delivering Order")
    
    deliver_result = deliver_order(order_id)
    if deliver_result:
        print(f"✅ Order Delivered!")
        print(f"   Status: {deliver_result.get('order', {}).get('status')}")
        print(f"   Delivered At: {deliver_result.get('order', {}).get('actual_delivery')}")
    
    # Final summary
    print_header("SCENARIO COMPLETE - SUMMARY")
    
    final_order = get_order(order_id)
    
    print(f"""
📋 Order Summary:
   Order ID: {order_id}
   Product: {sku}
   Quantity: {quantity}
   Store: {store_id}
   
🏭 Fulfillment:
   Warehouse: {final_order.get('assigned_warehouse')}
   Delivery: {final_order.get('delivery_id')}
   
📊 Status Flow:
   pending → allocated → shipped → delivered ✅
   
💰 Financials:
   Total Amount: ${final_order.get('total_amount', 0):.2f}
   
📦 Inventory Impact:
   SKU {sku} stock reduced by {quantity} units at {final_order.get('assigned_warehouse')}
""")
    
    print("\n✨ Example scenario completed successfully!")
    print("   Check the dashboard at http://localhost:8501 for visualization")


def main():
    """Main entry point"""
    try:
        run_example_scenario()
    except KeyboardInterrupt:
        print("\n\nScenario interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running scenario: {e}")
        raise


if __name__ == "__main__":
    main()
