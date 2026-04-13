"""
Streamlit Dashboard - Supply Chain Management System
Phase 3: Sensing & Intelligence Layer
"""
import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
import os

# Page configuration
st.set_page_config(
    page_title="Supply Chain Management Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding-top: 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 10px;
    }
    .status-pending { color: #FFA500; font-weight: bold; }
    .status-allocated { color: #1E90FF; font-weight: bold; }
    .status-shipped { color: #9370DB; font-weight: bold; }
    .status-delivered { color: #32CD32; font-weight: bold; }
    .status-cancelled { color: #DC143C; font-weight: bold; }
    .severity-critical { background-color: #ff4444; color: white; padding: 2px 8px; border-radius: 3px; }
    .severity-high { background-color: #ff8800; color: white; padding: 2px 8px; border-radius: 3px; }
    .severity-medium { background-color: #ffcc00; color: black; padding: 2px 8px; border-radius: 3px; }
    .severity-low { background-color: #88cc88; color: white; padding: 2px 8px; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# API base URL
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
# When switching backend to MongoDB Atlas, ensure the backend is configured with MONGODB_URI
# and this dashboard points to the correct backend API endpoint.

def fetch_kpis():
    """Fetch KPIs from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/dashboard/overview")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching KPIs: {e}")
        return None


def fetch_warehouse_stock():
    """Fetch warehouse stock data"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/dashboard/warehouse-stock")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching warehouse stock: {e}")
        return None


def fetch_low_stock(threshold=20):
    """Fetch low stock alerts"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/dashboard/low-stock?threshold={threshold}")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching low stock: {e}")
        return None


def fetch_metrics():
    """Fetch detailed metrics"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/dashboard/metrics")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching metrics: {e}")
        return None


def fetch_orders(status=None, limit=100):
    """Fetch orders from API"""
    try:
        url = f"{API_BASE_URL}/api/orders?limit={limit}"
        if status:
            url += f"&status={status}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching orders: {e}")
        return []


def fetch_deliveries(status=None, limit=100):
    """Fetch deliveries from API"""
    try:
        url = f"{API_BASE_URL}/api/deliveries?limit={limit}"
        if status:
            url += f"&status={status}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching deliveries: {e}")
        return []


def fetch_executions(limit=50):
    """Fetch execution logs from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/orders/executions/recent?limit={limit}")
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching executions: {e}")
        return []


def fetch_order_stats():
    """Fetch order statistics"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/orders/stats")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        return None


def fetch_delivery_stats():
    """Fetch delivery statistics"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/deliveries/stats")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        return None


def fetch_products(limit=100):
    """Fetch products"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/products?limit={limit}")
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        return []


def fetch_stores():
    """Fetch stores"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/stores")
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        return []


# ========================================
# INTELLIGENCE LAYER FUNCTIONS
# ========================================

def fetch_active_signals():
    """Fetch active signals from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/signals/active")
        if response.status_code == 200:
            return response.json()
        return {"signals": [], "count": 0}
    except Exception as e:
        st.error(f"Error fetching signals: {e}")
        return {"signals": [], "count": 0}


def fetch_signal_stats():
    """Fetch signal statistics"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/signals/stats")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        return None


def fetch_scheduler_status():
    """Fetch scheduler status"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/signals/scheduler/status")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        return None


def fetch_alerts_intelligence():
    """Fetch alerts from intelligence layer"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/signals/alerts?acknowledged=false&limit=50")
        if response.status_code == 200:
            return response.json()
        return {"alerts": [], "count": 0}
    except Exception as e:
        return {"alerts": [], "count": 0}


def fetch_replenishment_orders():
    """Fetch pending replenishment orders"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/signals/replenishment-orders")
        if response.status_code == 200:
            return response.json()
        return {"orders": [], "count": 0}
    except Exception as e:
        return {"orders": [], "count": 0}


def fetch_event_logs(limit=50):
    """Fetch event logs"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/signals/event-logs?limit={limit}")
        if response.status_code == 200:
            return response.json()
        return {"events": [], "count": 0}
    except Exception as e:
        return {"events": [], "count": 0}


def run_detection(detection_type):
    """Run a specific detection manually"""
    try:
        response = requests.post(f"{API_BASE_URL}/api/signals/detect/{detection_type}")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error running detection: {e}")
        return None


def acknowledge_signal_api(signal_id):
    """Acknowledge a signal"""
    try:
        response = requests.post(f"{API_BASE_URL}/api/signals/{signal_id}/acknowledge")
        return response.status_code == 200
    except Exception:
        return False


def resolve_signal_api(signal_id):
    """Resolve a signal"""
    try:
        response = requests.post(f"{API_BASE_URL}/api/signals/{signal_id}/resolve")
        return response.status_code == 200
    except Exception:
        return False


def main():
    """Main dashboard application"""
    st.title("📦 Supply Chain Management Dashboard")
    st.markdown("**Phase 3: Sensing & Intelligence Layer**")
    st.markdown("---")
    
    # Sidebar navigation
    page = st.sidebar.radio(
        "Navigate",
        ["Overview", "Intelligence", "Orders", "Deliveries", "Execution Logs", "Warehouses", "Stores", "Products", "Alerts"]
    )
    
    # Display selected page
    if page == "Overview":
        show_overview()
    elif page == "Intelligence":
        show_intelligence()
    elif page == "Orders":
        show_orders()
    elif page == "Deliveries":
        show_deliveries()
    elif page == "Execution Logs":
        show_execution_logs()
    elif page == "Warehouses":
        show_warehouses()
    elif page == "Stores":
        show_stores()
    elif page == "Products":
        show_products()
    elif page == "Alerts":
        show_alerts()


def show_overview():
    """Overview page with KPIs"""
    st.header("📊 System Overview")
    
    # Fetch KPIs
    kpis = fetch_kpis()
    order_stats = fetch_order_stats()
    delivery_stats = fetch_delivery_stats()
    
    if kpis:
        # KPI Cards - Row 1
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                label="Total Products",
                value=kpis.get("total_products", 0),
                delta=None
            )
        
        with col2:
            st.metric(
                label="Total Stock",
                value=f"{kpis.get('total_stock', 0):,}",
                delta=None
            )
        
        with col3:
            low_stock_alerts = kpis.get("low_stock_alerts", 0)
            st.metric(
                label="Low Stock Alerts",
                value=low_stock_alerts,
                delta=f"{'🔴' if low_stock_alerts > 0 else '✅'}"
            )
        
        with col4:
            st.metric(
                label="Warehouse Utilization",
                value=f"{kpis.get('warehouse_utilization', 0):.1f}%",
                delta=None
            )
        
        with col5:
            st.metric(
                label="Total Revenue",
                value=f"${kpis.get('total_revenue', 0):,.2f}",
                delta=None
            )
    
    # Order & Delivery Stats - Row 2
    if order_stats or delivery_stats:
        st.markdown("---")
        st.subheader("📋 Order & Delivery Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        if order_stats:
            with col1:
                st.metric(
                    label="Total Orders",
                    value=order_stats.get("total_orders", 0)
                )
            with col2:
                pending = order_stats.get("by_status", {}).get("pending", {}).get("count", 0)
                st.metric(
                    label="Pending Orders",
                    value=pending,
                    delta="⏳"
                )
        
        if delivery_stats:
            with col3:
                st.metric(
                    label="Total Deliveries",
                    value=delivery_stats.get("total_deliveries", 0)
                )
            with col4:
                in_transit = delivery_stats.get("by_status", {}).get("in_transit", {}).get("count", 0)
                st.metric(
                    label="In Transit",
                    value=in_transit,
                    delta="🚚"
                )
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Order Status Distribution
        if order_stats and order_stats.get("by_status"):
            st.subheader("Order Status Distribution")
            status_data = []
            for status, data in order_stats["by_status"].items():
                status_data.append({"Status": status.title(), "Count": data.get("count", 0)})
            
            if status_data:
                df = pd.DataFrame(status_data)
                fig = px.pie(df, values="Count", names="Status", 
                           color_discrete_sequence=px.colors.qualitative.Set2)
                st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Delivery by Transport Mode
        if delivery_stats and delivery_stats.get("by_transport_mode"):
            st.subheader("Deliveries by Transport Mode")
            mode_data = [{"Mode": mode.title(), "Count": count} 
                        for mode, count in delivery_stats["by_transport_mode"].items()]
            
            if mode_data:
                df = pd.DataFrame(mode_data)
                fig = px.bar(df, x="Mode", y="Count",
                           color="Mode",
                           color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig, use_container_width=True)


def show_orders():
    """Orders page"""
    st.header("📋 Orders Management")
    
    # Create Order Section
    with st.expander("➕ Create New Order", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        
        # Fetch products and stores for dropdowns
        products = fetch_products(limit=50)
        stores = fetch_stores()
        
        with col1:
            if products:
                product_options = {f"{p['name']} ({p['sku']})": p['sku'] for p in products}
                selected_product = st.selectbox("Select Product", list(product_options.keys()))
                sku = product_options.get(selected_product, "")
            else:
                sku = st.text_input("Product SKU")
        
        with col2:
            quantity = st.number_input("Quantity", min_value=1, value=10)
        
        with col3:
            if stores:
                store_options = {f"{s['name']} ({s['store_id']})": s['store_id'] for s in stores}
                selected_store = st.selectbox("Select Store", list(store_options.keys()))
                store_id = store_options.get(selected_store, "")
            else:
                store_id = st.text_input("Store ID")
        
        with col4:
            priority = st.selectbox("Priority", ["normal", "high", "low"])
        
        if st.button("Create Order", type="primary"):
            if sku and store_id:
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/api/orders/create",
                        json={"sku": sku, "quantity": quantity, "store_id": store_id, "priority": priority}
                    )
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"✅ Order created: {result['order']['order_id']}")
                        st.info("Use 'Process Order' to execute the order pipeline.")
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Error creating order: {e}")
            else:
                st.warning("Please fill in all required fields")
    
    st.markdown("---")
    
    # Filter controls
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "pending", "allocated", "shipped", "delivered", "cancelled"]
        )
    with col2:
        limit = st.slider("Max Results", 10, 200, 50)
    with col3:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    # Fetch orders
    status = None if status_filter == "All" else status_filter
    orders = fetch_orders(status=status, limit=limit)
    
    if orders:
        # Orders table
        st.subheader(f"Orders ({len(orders)} results)")
        
        for order in orders:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 2])
                
                with col1:
                    st.markdown(f"**{order['order_id']}**")
                    st.caption(f"Store: {order['store_id']}")
                
                with col2:
                    items = order.get('items', [])
                    if items:
                        st.write(f"SKU: {items[0]['sku']}")
                        st.caption(f"Qty: {items[0]['quantity']}")
                
                with col3:
                    status_color = {
                        "pending": "🟡",
                        "allocated": "🔵",
                        "shipped": "🟣",
                        "delivered": "🟢",
                        "cancelled": "🔴"
                    }
                    st.write(f"{status_color.get(order['status'], '⚪')} {order['status'].title()}")
                
                with col4:
                    st.write(f"₹{order.get('total_amount', 0):,.2f}")
                    st.caption(order.get('priority', 'normal').title())
                
                with col5:
                    # Action buttons
                    btn_col1, btn_col2, btn_col3 = st.columns(3)
                    
                    if order['status'] == 'pending':
                        with btn_col1:
                            if st.button("▶️ Process", key=f"process_{order['order_id']}"):
                                try:
                                    resp = requests.post(f"{API_BASE_URL}/api/orders/process/{order['order_id']}")
                                    if resp.status_code == 200:
                                        st.success("Order processed!")
                                        st.rerun()
                                    else:
                                        st.error(resp.json().get('detail', 'Error'))
                                except Exception as e:
                                    st.error(str(e))
                    
                    elif order['status'] == 'allocated':
                        with btn_col1:
                            if st.button("🚚 Ship", key=f"ship_{order['order_id']}"):
                                try:
                                    resp = requests.post(f"{API_BASE_URL}/api/orders/{order['order_id']}/ship")
                                    if resp.status_code == 200:
                                        st.success("Order shipped!")
                                        st.rerun()
                                    else:
                                        st.error(resp.json().get('detail', 'Error'))
                                except Exception as e:
                                    st.error(str(e))
                    
                    elif order['status'] == 'shipped':
                        with btn_col1:
                            if st.button("✅ Deliver", key=f"deliver_{order['order_id']}"):
                                try:
                                    resp = requests.post(f"{API_BASE_URL}/api/orders/{order['order_id']}/deliver")
                                    if resp.status_code == 200:
                                        st.success("Order delivered!")
                                        st.rerun()
                                    else:
                                        st.error(resp.json().get('detail', 'Error'))
                                except Exception as e:
                                    st.error(str(e))
                    
                    if order['status'] in ['pending', 'allocated']:
                        with btn_col2:
                            if st.button("❌ Cancel", key=f"cancel_{order['order_id']}"):
                                try:
                                    resp = requests.post(f"{API_BASE_URL}/api/orders/{order['order_id']}/cancel")
                                    if resp.status_code == 200:
                                        st.success("Order cancelled!")
                                        st.rerun()
                                    else:
                                        st.error(resp.json().get('detail', 'Error'))
                                except Exception as e:
                                    st.error(str(e))
                
                st.markdown("---")
    else:
        st.info("No orders found")


def show_deliveries():
    """Deliveries page"""
    st.header("🚚 Deliveries")
    
    # Filter controls
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "pending", "in_transit", "delivered", "failed", "cancelled"]
        )
    with col2:
        limit = st.slider("Max Results", 10, 200, 50, key="delivery_limit")
    with col3:
        if st.button("🔄 Refresh", key="refresh_deliveries"):
            st.rerun()
    
    # Fetch deliveries
    status = None if status_filter == "All" else status_filter
    deliveries = fetch_deliveries(status=status, limit=limit)
    
    # Stats
    delivery_stats = fetch_delivery_stats()
    if delivery_stats:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Deliveries", delivery_stats.get("total_deliveries", 0))
        with col2:
            in_transit = delivery_stats.get("by_status", {}).get("in_transit", {}).get("count", 0)
            st.metric("In Transit", in_transit)
        with col3:
            delivered = delivery_stats.get("by_status", {}).get("delivered", {}).get("count", 0)
            st.metric("Delivered", delivered)
        with col4:
            pending = delivery_stats.get("by_status", {}).get("pending", {}).get("count", 0)
            st.metric("Pending", pending)
    
    st.markdown("---")
    
    if deliveries:
        st.subheader(f"Deliveries ({len(deliveries)} results)")
        
        for delivery in deliveries:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 2])
                
                with col1:
                    st.markdown(f"**{delivery['delivery_id']}**")
                    st.caption(f"Order: {delivery['order_id']}")
                
                with col2:
                    st.write(f"📍 {delivery['warehouse_id']} → {delivery['store_id']}")
                    st.caption(f"Distance: {delivery.get('distance_km', 0):.1f} km")
                
                with col3:
                    st.write(f"🚛 {delivery.get('transport_mode', 'truck').title()}")
                    eta = delivery.get('estimated_duration_hours', 0)
                    st.caption(f"ETA: {eta:.1f} hours")
                
                with col4:
                    status_icon = {
                        "pending": "🟡",
                        "in_transit": "🔵",
                        "delivered": "🟢",
                        "failed": "🔴",
                        "cancelled": "⚫"
                    }
                    st.write(f"{status_icon.get(delivery['status'], '⚪')} {delivery['status'].replace('_', ' ').title()}")
                
                with col5:
                    if delivery['status'] == 'pending':
                        if st.button("▶️ Start", key=f"start_{delivery['delivery_id']}"):
                            try:
                                resp = requests.post(f"{API_BASE_URL}/api/deliveries/{delivery['delivery_id']}/start")
                                if resp.status_code == 200:
                                    st.success("Delivery started!")
                                    st.rerun()
                                else:
                                    st.error(resp.json().get('detail', 'Error'))
                            except Exception as e:
                                st.error(str(e))
                    
                    elif delivery['status'] == 'in_transit':
                        if st.button("✅ Complete", key=f"complete_{delivery['delivery_id']}"):
                            try:
                                resp = requests.post(f"{API_BASE_URL}/api/deliveries/{delivery['delivery_id']}/complete")
                                if resp.status_code == 200:
                                    st.success("Delivery completed!")
                                    st.rerun()
                                else:
                                    st.error(resp.json().get('detail', 'Error'))
                            except Exception as e:
                                st.error(str(e))
                
                st.markdown("---")
    else:
        st.info("No deliveries found")


def show_execution_logs():
    """Execution logs page"""
    st.header("📜 Execution Logs")
    st.markdown("Track all order processing decisions and steps")
    
    # Fetch executions
    col1, col2 = st.columns([3, 1])
    with col1:
        limit = st.slider("Number of Executions", 10, 100, 30)
    with col2:
        if st.button("🔄 Refresh", key="refresh_logs"):
            st.rerun()
    
    executions = fetch_executions(limit=limit)
    
    if executions:
        for execution in executions:
            status_icon = "✅" if execution['status'] == 'completed' else "❌" if execution['status'] == 'failed' else "⏳"
            
            with st.expander(
                f"{status_icon} {execution['execution_id']} | Order: {execution['order_id']} | {execution['status'].title()}",
                expanded=False
            ):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Execution ID:** {execution['execution_id']}")
                    st.write(f"**Order ID:** {execution['order_id']}")
                    st.write(f"**Status:** {execution['status']}")
                
                with col2:
                    if execution.get('started_at'):
                        st.write(f"**Started:** {execution['started_at']}")
                    if execution.get('completed_at'):
                        st.write(f"**Completed:** {execution['completed_at']}")
                
                # Show execution steps
                if execution.get('steps'):
                    st.markdown("**Execution Steps:**")
                    for step in execution['steps']:
                        level_icon = {
                            "info": "ℹ️",
                            "success": "✅",
                            "warning": "⚠️",
                            "error": "❌"
                        }
                        icon = level_icon.get(step.get('level', 'info'), 'ℹ️')
                        st.markdown(f"{icon} **{step['step']}**: {step['message']}")
                        
                        if step.get('details') and st.checkbox(f"Show details", key=f"details_{execution['execution_id']}_{step['step_id']}"):
                            st.json(step['details'])
                
                # Show summary
                if execution.get('summary'):
                    st.markdown("**Summary:**")
                    st.json(execution['summary'])
                
                # Show error if failed
                if execution.get('error'):
                    st.error(f"**Error:** {execution['error'].get('message', 'Unknown error')}")
    else:
        st.info("No execution logs found. Process some orders to see execution logs here.")


def show_warehouses():
    """Warehouses page"""
    st.header("🏭 Warehouses")
    
    warehouse_data = fetch_warehouse_stock()
    
    if warehouse_data and "warehouses" in warehouse_data:
        warehouses = warehouse_data["warehouses"]
        
        # Create DataFrame
        df = pd.DataFrame(warehouses)
        
        if not df.empty:
            # Display table
            st.subheader("Warehouse Inventory")
            st.dataframe(df, use_container_width=True)
            
            # Utilization chart
            st.subheader("Warehouse Utilization")
            fig = px.bar(
                df,
                x="warehouse_id",
                y="utilization_rate",
                title="Warehouse Utilization Rate (%)",
                labels={"warehouse_id": "Warehouse", "utilization_rate": "Utilization %"},
                color="utilization_rate",
                color_continuous_scale="RdYlGn"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Stock by warehouse
            if "current_utilization" in df.columns:
                st.subheader("Stock by Warehouse")
                fig = px.bar(
                    df,
                    x="warehouse_id",
                    y="current_utilization",
                    title="Current Stock by Warehouse",
                    labels={"warehouse_id": "Warehouse", "current_utilization": "Stock Units"}
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No warehouse data available")


def show_stores():
    """Stores page"""
    st.header("🏪 Stores")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/stores")
        if response.status_code == 200:
            stores = response.json()
            
            if stores:
                df = pd.DataFrame(stores)
                
                # Display table
                st.subheader("Store Inventory")
                st.dataframe(df, use_container_width=True)
                
                # Stock by store
                if "current_utilization" in df.columns:
                    st.subheader("Stock by Store")
                    fig = px.bar(
                        df,
                        x="store_id",
                        y="current_utilization",
                        title="Current Stock by Store",
                        labels={"store_id": "Store", "current_utilization": "Stock Units"}
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No store data available")
    except Exception as e:
        st.error(f"Error fetching store data: {e}")


def show_products():
    """Products page"""
    st.header("📦 Products")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/products?limit=50")
        if response.status_code == 200:
            products = response.json()
            
            if products:
                df = pd.DataFrame(products)
                
                # Filters
                col1, col2 = st.columns(2)
                with col1:
                    category_filter = st.selectbox(
                        "Filter by Category",
                        ["All"] + list(df["category"].unique()) if "category" in df.columns else ["All"]
                    )
                
                with col2:
                    brand_filter = st.selectbox(
                        "Filter by Brand",
                        ["All"] + list(df["brand"].unique()) if "brand" in df.columns else ["All"]
                    )
                
                # Apply filters
                if category_filter != "All" and "category" in df.columns:
                    df = df[df["category"] == category_filter]
                if brand_filter != "All" and "brand" in df.columns:
                    df = df[df["brand"] == brand_filter]
                
                # Display table
                st.subheader("Product Catalog")
                st.dataframe(df, use_container_width=True)
                
                # Sales by product
                if "total_sales" in df.columns and "name" in df.columns:
                    st.subheader("Sales by Product")
                    fig = px.bar(
                        df.head(10),
                        x="name",
                        y="total_sales",
                        title="Top 10 Products by Sales",
                        labels={"total_sales": "Units Sold", "name": "Product"}
                    )
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No product data available")
    except Exception as e:
        st.error(f"Error fetching product data: {e}")


def show_alerts():
    """Alerts page"""
    st.header("🚨 Alerts")
    
    # Low stock alerts
    st.subheader("Low Stock Alerts")
    low_stock_data = fetch_low_stock(threshold=20)
    
    if low_stock_data and low_stock_data.get("count", 0) > 0:
        items = low_stock_data.get("items", [])
        df = pd.DataFrame(items)
        
        # Add severity column
        if "quantity" in df.columns:
            df["severity"] = df["quantity"].apply(lambda x: "Critical" if x < 10 else "Warning")
        
        # Color code severity
        def highlight_severity(val):
            if val == "Critical":
                return 'background-color: #ffcccc'
            elif val == "Warning":
                return 'background-color: #fff3cd'
            return ''
        
        if not df.empty:
            st.dataframe(
                df.style.applymap(highlight_severity, subset=['severity']),
                use_container_width=True
            )
            
            # Summary
            critical_count = len(df[df["severity"] == "Critical"]) if "severity" in df.columns else 0
            warning_count = len(df[df["severity"] == "Warning"]) if "severity" in df.columns else 0
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Critical Alerts", critical_count, delta="🔴")
            with col2:
                st.metric("Warning Alerts", warning_count, delta="⚠️")
    else:
        st.success("✅ No low stock alerts at this time!")
    
    st.markdown("---")
    
    # Fetch all alerts
    metrics = fetch_metrics()
    if metrics and "alerts" in metrics:
        st.subheader("All System Alerts")
        all_alerts = metrics["alerts"]
        
        if all_alerts:
            for alert in all_alerts:
                severity = alert.get("severity", "info")
                icon = "🔴" if severity == "critical" else "⚠️" if severity == "warning" else "ℹ️"
                
                with st.expander(f"{icon} {alert.get('type', 'Alert').title()} - {severity.title()}", expanded=severity == "critical"):
                    st.write(f"**Message:** {alert.get('message', 'No message')}")
                    if "details" in alert:
                        st.json(alert["details"])
        else:
            st.info("No system alerts")


# ========================================
# INTELLIGENCE PANEL
# ========================================

def show_intelligence():
    """Intelligence Panel - Sensing & Monitoring"""
    st.header("Intelligence Panel")
    st.markdown("*Real-time monitoring, signal detection, and automated responses*")
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview", "🚨 Active Signals", "⚡ Scheduler", "📋 Event Logs", "🔧 Manual Controls"
    ])
    
    with tab1:
        show_intelligence_overview()
    
    with tab2:
        show_active_signals()
    
    with tab3:
        show_scheduler_status()
    
    with tab4:
        show_event_logs()
    
    with tab5:
        show_manual_controls()


def show_intelligence_overview():
    """Intelligence overview with stats"""
    st.subheader("System Intelligence Overview")
    
    # Fetch stats
    signal_stats = fetch_signal_stats()
    scheduler_status = fetch_scheduler_status()
    alerts_data = fetch_alerts_intelligence()
    replenishment_data = fetch_replenishment_orders()
    
    # KPI Row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        active_signals = signal_stats.get("active_signals", 0) if signal_stats else 0
        st.metric(
            "Active Signals",
            active_signals,
            delta="🔴" if active_signals > 0 else "✅"
        )
    
    with col2:
        total_signals = signal_stats.get("total_signals", 0) if signal_stats else 0
        st.metric("Total Signals", total_signals)
    
    with col3:
        recent_24h = signal_stats.get("recent_24h", 0) if signal_stats else 0
        st.metric("Signals (24h)", recent_24h)
    
    with col4:
        unack_alerts = alerts_data.get("count", 0)
        st.metric(
            "Unread Alerts",
            unack_alerts,
            delta="⚠️" if unack_alerts > 0 else "✅"
        )
    
    with col5:
        pending_orders = replenishment_data.get("count", 0)
        st.metric(
            "Pending Replenishment",
            pending_orders,
            delta="📦" if pending_orders > 0 else "✅"
        )
    
    st.markdown("---")
    
    # Charts Row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Signals by Type")
        if signal_stats and signal_stats.get("by_type"):
            by_type = signal_stats["by_type"]
            if by_type:
                df = pd.DataFrame([
                    {"Type": k, "Count": v} for k, v in by_type.items()
                ])
                fig = px.pie(df, values="Count", names="Type", title="Signal Distribution by Type")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No signal data available")
        else:
            st.info("No signal statistics available")
    
    with col2:
        st.subheader("Signals by Severity")
        if signal_stats and signal_stats.get("by_severity"):
            by_severity = signal_stats["by_severity"]
            if by_severity:
                # Define color map
                color_map = {
                    "critical": "#ff4444",
                    "high": "#ff8800",
                    "medium": "#ffcc00",
                    "low": "#88cc88"
                }
                df = pd.DataFrame([
                    {"Severity": k, "Count": v} for k, v in by_severity.items()
                ])
                fig = px.bar(
                    df, x="Severity", y="Count",
                    title="Signal Distribution by Severity",
                    color="Severity",
                    color_discrete_map=color_map
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No severity data available")
        else:
            st.info("No severity statistics available")
    
    # Scheduler Status
    st.markdown("---")
    st.subheader("Scheduler Status")
    
    if scheduler_status:
        # Status and controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            running = scheduler_status.get("is_running", False)
            st.metric(
                "Scheduler",
                "Running" if running else "Stopped",
                delta="🟢" if running else "🔴"
            )
        
        with col2:
            job_count = scheduler_status.get("job_count", 0)
            st.metric("Active Jobs", job_count)
        
        with col3:
            st.metric("State", scheduler_status.get("state", "Unknown"))
    else:
        st.warning("Cannot fetch scheduler status")


def show_active_signals():
    """Display active signals"""
    st.subheader("Active Signals")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        type_filter = st.selectbox(
            "Signal Type",
            ["All", "LOW_STOCK", "STOCKOUT", "OVERSTOCK", "DEMAND_SPIKE", 
             "DEMAND_DROP", "DELIVERY_DELAY", "OVER_UTILIZATION", "UNDER_UTILIZATION"]
        )
    with col2:
        severity_filter = st.selectbox(
            "Severity",
            ["All", "critical", "high", "medium", "low"]
        )
    with col3:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    # Fetch signals
    signals_data = fetch_active_signals()
    signals = signals_data.get("signals", [])
    
    # Apply filters
    if type_filter != "All":
        signals = [s for s in signals if s.get("type") == type_filter]
    if severity_filter != "All":
        signals = [s for s in signals if s.get("severity") == severity_filter]
    
    if signals:
        st.write(f"**{len(signals)} active signals**")
        
        for signal in signals:
            severity = signal.get("severity", "medium")
            signal_type = signal.get("type", "UNKNOWN")
            
            # Severity icons
            severity_icons = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢"
            }
            icon = severity_icons.get(severity, "⚪")
            
            with st.expander(
                f"{icon} {signal_type} - {signal.get('entity_type', '')} {signal.get('entity_id', '')}",
                expanded=(severity == "critical")
            ):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Message:** {signal.get('message', 'No message')}")
                    st.write(f"**Signal ID:** `{signal.get('signal_id', 'N/A')}`")
                    st.write(f"**Severity:** {severity.upper()}")
                    st.write(f"**Created:** {signal.get('created_at', 'N/A')}")
                    
                    if signal.get("details"):
                        st.json(signal["details"])
                
                with col2:
                    signal_id = signal.get("signal_id")
                    if st.button("✅ Acknowledge", key=f"ack_{signal_id}"):
                        if acknowledge_signal_api(signal_id):
                            st.success("Acknowledged!")
                            st.rerun()
                        else:
                            st.error("Failed to acknowledge")
                    
                    if st.button("🔧 Resolve", key=f"resolve_{signal_id}"):
                        if resolve_signal_api(signal_id):
                            st.success("Resolved!")
                            st.rerun()
                        else:
                            st.error("Failed to resolve")
    else:
        st.success("✅ No active signals - system is healthy!")


def show_scheduler_status():
    """Display scheduler status and jobs"""
    st.subheader("Background Scheduler")
    
    scheduler_status = fetch_scheduler_status()
    
    if scheduler_status:
        # Status and controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            running = scheduler_status.get("is_running", False)
            st.metric(
                "Status",
                "Running" if running else "Stopped",
                delta="🟢" if running else "🔴"
            )
        
        with col2:
            if st.button("▶️ Start Scheduler"):
                try:
                    response = requests.post(f"{API_BASE_URL}/api/signals/scheduler/start")
                    if response.status_code == 200:
                        st.success("Scheduler started!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        
        with col3:
            if st.button("⏹️ Stop Scheduler"):
                try:
                    response = requests.post(f"{API_BASE_URL}/api/signals/scheduler/stop")
                    if response.status_code == 200:
                        st.success("Scheduler stopped!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        
        st.markdown("---")
        
        # Jobs list
        st.subheader("Scheduled Jobs")
        jobs = scheduler_status.get("jobs", [])
        
        if jobs:
            for job in jobs:
                job_id = job.get("id", "Unknown")
                job_name = job.get("name", job_id)
                next_run = job.get("next_run", "N/A")
                runs = job.get("runs", 0)
                errors = job.get("errors", 0)
                
                with st.expander(f"🕐 {job_name}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Job ID:** `{job_id}`")
                        st.write(f"**Next Run:** {next_run}")
                        st.write(f"**Trigger:** {job.get('trigger', 'N/A')}")
                    
                    with col2:
                        st.metric("Total Runs", runs)
                        st.metric("Errors", errors, delta="🔴" if errors > 0 else None)
                    
                    with col3:
                        if st.button("▶️ Run Now", key=f"run_{job_id}"):
                            try:
                                response = requests.post(f"{API_BASE_URL}/api/signals/scheduler/jobs/{job_id}/run")
                                if response.status_code == 200:
                                    st.success(f"Job {job_id} executed!")
                                    st.rerun()
                                else:
                                    st.error("Failed to run job")
                            except Exception as e:
                                st.error(f"Error: {e}")
        else:
            st.info("No scheduled jobs")
    else:
        st.warning("Cannot fetch scheduler status. Make sure the API is running.")


def show_event_logs():
    """Display event logs"""
    st.subheader("Event Logs")
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        event_type_filter = st.selectbox(
            "Event Type",
            ["All", "signal_created", "signal_resolved", "action_executed", "detection_run"]
        )
    with col2:
        limit = st.slider("Max Events", 10, 100, 50)
    
    # Fetch logs
    logs_data = fetch_event_logs(limit=limit)
    events = logs_data.get("events", [])
    
    if event_type_filter != "All":
        events = [e for e in events if e.get("event_type") == event_type_filter]
    
    if events:
        st.write(f"**{len(events)} events**")
        
        df = pd.DataFrame(events)
        
        # Select columns to display
        display_cols = ["event_id", "event_type", "action", "status", "source", "timestamp"]
        available_cols = [c for c in display_cols if c in df.columns]
        
        if available_cols:
            st.dataframe(df[available_cols], use_container_width=True)
        
        # Detailed view
        st.subheader("Event Details")
        for event in events[:10]:
            event_type = event.get("event_type", "unknown")
            status = event.get("status", "unknown")
            
            status_icon = "✅" if status == "success" else "❌" if status == "failed" else "⏳"
            
            with st.expander(f"{status_icon} {event_type} - {event.get('timestamp', 'N/A')}"):
                st.write(f"**Event ID:** `{event.get('event_id', 'N/A')}`")
                st.write(f"**Signal ID:** `{event.get('signal_id', 'N/A')}`")
                st.write(f"**Action:** {event.get('action', 'N/A')}")
                st.write(f"**Source:** {event.get('source', 'N/A')}")
                
                if event.get("metadata"):
                    st.json(event["metadata"])
                
                if event.get("error"):
                    st.error(f"Error: {event['error']}")
    else:
        st.info("No event logs available")


def show_manual_controls():
    """Manual detection controls"""
    st.subheader("Manual Detection Controls")
    st.markdown("*Run detection functions manually for testing or immediate checks*")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Inventory Detections")
        
        if st.button("🔍 Detect Low Stock", use_container_width=True):
            with st.spinner("Running low stock detection..."):
                result = run_detection("low-stock")
                if result:
                    st.success(f"✅ Low Stock: {result.get('signals_generated', 0)} signals from {result.get('items_checked', 0)} items")
                    st.json(result)
        
        if st.button("🚨 Detect Stockout", use_container_width=True):
            with st.spinner("Running stockout detection..."):
                result = run_detection("stockout")
                if result:
                    st.success(f"✅ Stockout: {result.get('signals_generated', 0)} signals from {result.get('items_checked', 0)} items")
                    st.json(result)
        
        st.markdown("### Delivery Detections")
        
        if st.button("🚚 Detect Delivery Delays", use_container_width=True):
            with st.spinner("Running delivery delay detection..."):
                result = run_detection("delivery-delay")
                if result:
                    st.success(f"✅ Delivery Delays: {result.get('signals_generated', 0)} signals from {result.get('deliveries_checked', 0)} deliveries")
                    st.json(result)
    
    with col2:
        st.markdown("### Demand Detections")
        
        if st.button("📈 Detect Demand Spike", use_container_width=True):
            with st.spinner("Running demand spike detection..."):
                result = run_detection("demand-spike")
                if result:
                    st.success(f"✅ Demand Spike: {'Detected!' if result.get('spike_detected') else 'Not detected'}")
                    st.json(result)
        
        st.markdown("### Warehouse Detections")
        
        if st.button("🏭 Detect Utilization Issues", use_container_width=True):
            with st.spinner("Running utilization detection..."):
                result = run_detection("utilization")
                if result:
                    over = result.get("over_utilization", {})
                    under = result.get("under_utilization", {})
                    st.success(f"✅ Over: {over.get('signals_generated', 0)}, Under: {under.get('signals_generated', 0)} signals")
                    st.json(result)
        
        st.markdown("### Run All")
        
        if st.button("🔄 Run All Detections", type="primary", use_container_width=True):
            with st.spinner("Running all detections..."):
                try:
                    response = requests.post(f"{API_BASE_URL}/api/signals/detect/all")
                    if response.status_code == 200:
                        result = response.json()
                        total = result.get("total_signals_generated", 0)
                        st.success(f"✅ All detections complete! {total} total signals generated")
                        st.json(result)
                    else:
                        st.error("Failed to run detections")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    st.markdown("---")
    
    # Replenishment Orders
    st.subheader("Pending Replenishment Orders")
    replenishment_data = fetch_replenishment_orders()
    orders = replenishment_data.get("orders", [])
    
    if orders:
        for order in orders:
            order_id = order.get("order_id", "Unknown")
            sku = order.get("items", [{}])[0].get("sku", "N/A")
            qty = order.get("items", [{}])[0].get("quantity", 0)
            warehouse_id = order.get("warehouse_id", "N/A")
            
            with st.expander(f"📦 {order_id} - {sku} ({qty} units)"):
                st.write(f"**Order ID:** `{order_id}`")
                st.write(f"**Warehouse:** {warehouse_id}")
                st.write(f"**Supplier:** {order.get('supplier_id', 'N/A')}")
                st.write(f"**Priority:** {order.get('priority', 'N/A')}")
                st.write(f"**Created:** {order.get('created_at', 'N/A')}")
                
                if st.button("✅ Approve Order", key=f"approve_{order_id}"):
                    try:
                        response = requests.post(f"{API_BASE_URL}/api/signals/replenishment-orders/{order_id}/approve")
                        if response.status_code == 200:
                            st.success("Order approved!")
                            st.rerun()
                        else:
                            st.error("Failed to approve order")
                    except Exception as e:
                        st.error(f"Error: {e}")
    else:
        st.success("✅ No pending replenishment orders")


if __name__ == "__main__":
    main()
