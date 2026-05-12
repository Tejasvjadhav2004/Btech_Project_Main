"""Create sample execution logs for testing"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from db.connection import mongodb
from datetime import datetime, timedelta
import random

# Connect to database
print("Connecting to MongoDB...")
mongodb.connect()
db = mongodb.get_database()

# Clear existing execution logs
db.execution_logs.delete_many({})
print("Cleared existing execution logs")

# Sample execution logs
now = datetime.now()
sample_executions = [
    {
        "execution_id": "EXE-ABC12345",
        "order_id": "ORD-SAMPLE001",
        "status": "completed",
        "started_at": now - timedelta(hours=2),
        "completed_at": now - timedelta(hours=1, minutes=50),
        "steps": [
            {"step_id": "S001", "step": "order_created", "message": "Order created successfully", "status": "success"},
            {"step_id": "S002", "step": "order_validated", "message": "Order validated", "status": "success"},
            {"step_id": "S003", "step": "warehouse_selected", "message": "Warehouse WH001 selected", "status": "success"},
            {"step_id": "S004", "step": "inventory_allocated", "message": "Inventory allocated: 50 units", "status": "success"},
            {"step_id": "S005", "step": "delivery_created", "message": "Delivery created", "status": "success"}
        ]
    },
    {
        "execution_id": "EXE-DEF67890",
        "order_id": "ORD-SAMPLE002",
        "status": "failed",
        "started_at": now - timedelta(hours=1, minutes=30),
        "completed_at": now - timedelta(hours=1, minutes=20),
        "error": {
            "message": "Insufficient inventory in warehouse WH002",
            "code": "INSUFFICIENT_INVENTORY"
        },
        "steps": [
            {"step_id": "S001", "step": "order_created", "message": "Order created successfully", "status": "success"},
            {"step_id": "S002", "step": "order_validated", "message": "Order validated", "status": "success"},
            {"step_id": "S003", "step": "warehouse_selected", "message": "Warehouse WH002 selected", "status": "success"},
            {"step_id": "S004", "step": "inventory_allocated", "message": "Failed to allocate inventory", "status": "failed"}
        ]
    },
    {
        "execution_id": "EXE-GHI01234",
        "order_id": "ORD-SAMPLE003",
        "status": "completed",
        "started_at": now - timedelta(hours=1),
        "completed_at": now - timedelta(minutes=50),
        "steps": [
            {"step_id": "S001", "step": "order_created", "message": "Order created successfully", "status": "success"},
            {"step_id": "S002", "step": "order_validated", "message": "Order validated", "status": "success"},
            {"step_id": "S003", "step": "warehouse_selected", "message": "Warehouse WH003 selected", "status": "success"},
            {"step_id": "S004", "step": "inventory_allocated", "message": "Inventory allocated: 100 units", "status": "success"},
            {"step_id": "S005", "step": "delivery_created", "message": "Delivery created", "status": "success"}
        ]
    },
    {
        "execution_id": "EXE-JKL56789",
        "order_id": "ORD-SAMPLE004",
        "status": "completed",
        "started_at": now - timedelta(minutes=45),
        "completed_at": now - timedelta(minutes=35),
        "steps": [
            {"step_id": "S001", "step": "order_created", "message": "Order created successfully", "status": "success"},
            {"step_id": "S002", "step": "order_validated", "message": "Order validated", "status": "success"},
            {"step_id": "S003", "step": "warehouse_selected", "message": "Warehouse WH004 selected", "status": "success"},
            {"step_id": "S004", "step": "inventory_allocated", "message": "Inventory allocated: 75 units", "status": "success"},
            {"step_id": "S005", "step": "delivery_created", "message": "Delivery created", "status": "success"}
        ]
    },
    {
        "execution_id": "EXE-MNO34567",
        "order_id": "ORD-SAMPLE005",
        "status": "failed",
        "started_at": now - timedelta(minutes=30),
        "completed_at": now - timedelta(minutes=25),
        "error": {
            "message": "Delivery service unavailable",
            "code": "SERVICE_UNAVAILABLE"
        },
        "steps": [
            {"step_id": "S001", "step": "order_created", "message": "Order created successfully", "status": "success"},
            {"step_id": "S002", "step": "order_validated", "message": "Order validated", "status": "success"},
            {"step_id": "S003", "step": "warehouse_selected", "message": "Warehouse WH001 selected", "status": "success"},
            {"step_id": "S004", "step": "inventory_allocated", "message": "Inventory allocated: 25 units", "status": "success"},
            {"step_id": "S005", "step": "delivery_created", "message": "Failed to create delivery", "status": "failed"}
        ]
    },
    {
        "execution_id": "EXE-PQR89012",
        "order_id": "ORD-SAMPLE006",
        "status": "completed",
        "started_at": now - timedelta(minutes=20),
        "completed_at": now - timedelta(minutes=15),
        "steps": [
            {"step_id": "S001", "step": "order_created", "message": "Order created successfully", "status": "success"},
            {"step_id": "S002", "step": "order_validated", "message": "Order validated", "status": "success"},
            {"step_id": "S003", "step": "warehouse_selected", "message": "Warehouse WH005 selected", "status": "success"},
            {"step_id": "S004", "step": "inventory_allocated", "message": "Inventory allocated: 150 units", "status": "success"},
            {"step_id": "S005", "step": "delivery_created", "message": "Delivery created", "status": "success"}
        ]
    },
    {
        "execution_id": "EXE-STU45678",
        "order_id": "ORD-SAMPLE007",
        "status": "completed",
        "started_at": now - timedelta(minutes=10),
        "completed_at": now - timedelta(minutes=8),
        "steps": [
            {"step_id": "S001", "step": "order_created", "message": "Order created successfully", "status": "success"},
            {"step_id": "S002", "step": "order_validated", "message": "Order validated", "status": "success"},
            {"step_id": "S003", "step": "warehouse_selected", "message": "Warehouse WH001 selected", "status": "success"},
            {"step_id": "S004", "step": "inventory_allocated", "message": "Inventory allocated: 80 units", "status": "success"},
            {"step_id": "S005", "step": "delivery_created", "message": "Delivery created", "status": "success"}
        ]
    },
    {
        "execution_id": "EXE-VWX34567",
        "order_id": "ORD-SAMPLE008",
        "status": "completed",
        "started_at": now - timedelta(minutes=5),
        "completed_at": now - timedelta(minutes=3),
        "steps": [
            {"step_id": "S001", "step": "order_created", "message": "Order created successfully", "status": "success"},
            {"step_id": "S002", "step": "order_validated", "message": "Order validated", "status": "success"},
            {"step_id": "S003", "step": "warehouse_selected", "message": "Warehouse WH003 selected", "status": "success"},
            {"step_id": "S004", "step": "inventory_allocated", "message": "Inventory allocated: 120 units", "status": "success"},
            {"step_id": "S005", "step": "delivery_created", "message": "Delivery created", "status": "success"}
        ]
    },
    {
        "execution_id": "EXE-YZA89012",
        "order_id": "ORD-SAMPLE009",
        "status": "completed",
        "started_at": now - timedelta(minutes=2),
        "completed_at": now - timedelta(minutes=1),
        "steps": [
            {"step_id": "S001", "step": "order_created", "message": "Order created successfully", "status": "success"},
            {"step_id": "S002", "step": "order_validated", "message": "Order validated", "status": "success"},
            {"step_id": "S003", "step": "warehouse_selected", "message": "Warehouse WH002 selected", "status": "success"},
            {"step_id": "S004", "step": "inventory_allocated", "message": "Inventory allocated: 60 units", "status": "success"},
            {"step_id": "S005", "step": "delivery_created", "message": "Delivery created", "status": "success"}
        ]
    },
    {
        "execution_id": "EXE-BCD56789",
        "order_id": "ORD-SAMPLE010",
        "status": "completed",
        "started_at": now - timedelta(minutes=1),
        "completed_at": now - timedelta(seconds=30),
        "steps": [
            {"step_id": "S001", "step": "order_created", "message": "Order created successfully", "status": "success"},
            {"step_id": "S002", "step": "order_validated", "message": "Order validated", "status": "success"},
            {"step_id": "S003", "step": "warehouse_selected", "message": "Warehouse WH004 selected", "status": "success"},
            {"step_id": "S004", "step": "inventory_allocated", "message": "Inventory allocated: 90 units", "status": "success"},
            {"step_id": "S005", "step": "delivery_created", "message": "Delivery created", "status": "success"}
        ]
    }
]

# Insert sample execution logs
print(f"Inserting {len(sample_executions)} sample execution logs...")
db.execution_logs.insert_many(sample_executions)
print("Sample execution logs created successfully!")

# Verify
count = db.execution_logs.count_documents({})
print(f"\nTotal execution logs in database: {count}")

print("\nSample execution logs created! Refresh your browser to see them in the System Logs & Anomalies page.")
