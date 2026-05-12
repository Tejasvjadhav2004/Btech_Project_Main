"""
MongoDB Collection Setup for Phase 3: Sensing & Intelligence Layer

This module handles the creation and indexing of signals and event_logs collections.
"""
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import CollectionInvalid
from db.connection import mongodb
import logging

logger = logging.getLogger(__name__)


def setup_signals_collection(db):
    """
    Set up the signals collection with proper indexes.
    
    Collection Schema:
    {
        "signal_id": "SIG-XXXXXXXX",
        "type": "LOW_STOCK|STOCKOUT|DEMAND_SPIKE|...",
        "entity_type": "warehouse|store|delivery|product",
        "entity_id": "string",
        "product_id": "string (optional)",
        "severity": "low|medium|high|critical",
        "status": "active|acknowledged|resolved|expired",
        "message": "Human-readable description",
        "details": { ... },
        "threshold": { ... },
        "created_at": datetime,
        "acknowledged_at": datetime,
        "resolved_at": datetime,
        "auto_resolved": bool,
        "action_taken": { ... }
    }
    """
    collection_name = "signals"
    collection = db[collection_name]
    
    # Create indexes
    indexes_created = []
    
    # Unique index on signal_id
    collection.create_index("signal_id", unique=True)
    indexes_created.append("signal_id (unique)")
    
    # Compound index for duplicate prevention - only one active signal per entity/type/product
    collection.create_index(
        [
            ("type", ASCENDING),
            ("entity_type", ASCENDING),
            ("entity_id", ASCENDING),
            ("product_id", ASCENDING),
            ("status", ASCENDING)
        ],
        name="duplicate_prevention_idx",
        partialFilterExpression={"status": "active"}
    )
    indexes_created.append("duplicate_prevention_idx (compound)")
    
    # Index for querying active signals
    collection.create_index(
        [("status", ASCENDING), ("severity", DESCENDING)],
        name="active_signals_idx"
    )
    indexes_created.append("active_signals_idx")
    
    # Index for time-based queries
    collection.create_index(
        [("created_at", DESCENDING)],
        name="created_at_idx"
    )
    indexes_created.append("created_at_idx")
    
    # Index for entity lookups
    collection.create_index(
        [("entity_type", ASCENDING), ("entity_id", ASCENDING)],
        name="entity_lookup_idx"
    )
    indexes_created.append("entity_lookup_idx")
    
    # Index for type-based queries
    collection.create_index("type", name="type_idx")
    indexes_created.append("type_idx")
    
    # Index for severity-based queries
    collection.create_index("severity", name="severity_idx")
    indexes_created.append("severity_idx")
    
    logger.info(f"Signals collection setup complete. Indexes: {indexes_created}")
    return collection


def setup_event_logs_collection(db):
    """
    Set up the event_logs collection with proper indexes.
    
    Collection Schema:
    {
        "event_id": "EVT-XXXXXXXX",
        "signal_id": "SIG-XXXXXXXX (optional)",
        "event_type": "signal_created|action_executed|...",
        "action": "create_replenishment_order|send_alert|...",
        "status": "success|failed|skipped",
        "source": "scheduler|event_trigger|manual",
        "metadata": { ... },
        "error": { ... },
        "timestamp": datetime
    }
    """
    collection_name = "event_logs"
    collection = db[collection_name]
    
    # Create indexes
    indexes_created = []
    
    # Unique index on event_id
    collection.create_index("event_id", unique=True)
    indexes_created.append("event_id (unique)")
    
    # Index for signal lookups
    collection.create_index("signal_id", name="signal_id_idx")
    indexes_created.append("signal_id_idx")
    
    # Index for time-based queries
    collection.create_index(
        [("timestamp", DESCENDING)],
        name="timestamp_idx"
    )
    indexes_created.append("timestamp_idx")
    
    # Index for event type queries
    collection.create_index("event_type", name="event_type_idx")
    indexes_created.append("event_type_idx")
    
    # Compound index for filtering
    collection.create_index(
        [("event_type", ASCENDING), ("status", ASCENDING), ("timestamp", DESCENDING)],
        name="filter_idx"
    )
    indexes_created.append("filter_idx")
    
    # Index for source-based queries
    collection.create_index("source", name="source_idx")
    indexes_created.append("source_idx")
    
    # TTL index to auto-expire old event logs after 90 days
    collection.create_index(
        "timestamp",
        name="ttl_idx",
        expireAfterSeconds=90 * 24 * 60 * 60  # 90 days
    )
    indexes_created.append("ttl_idx (90 days)")
    
    logger.info(f"Event logs collection setup complete. Indexes: {indexes_created}")
    return collection


def setup_intelligence_collections():
    """
    Set up all collections for the Sensing & Intelligence Layer.
    Call this on application startup.
    """
    db = mongodb.get_database()
    if db is None:
        logger.error("Database connection not available")
        return False

    try:
        signals_collection = setup_signals_collection(db)
        event_logs_collection = setup_event_logs_collection(db)
        predictions_collection = setup_predictions_collection(db)
        predictive_risks_collection = setup_predictive_risks_collection(db)

        logger.info("Intelligence Layer collections setup complete (including predictive collections)")
        return True
    except Exception as e:
        logger.error(f"Error setting up intelligence collections: {e}")
        return False


def get_signals_collection():
    """Get the signals collection"""
    db = mongodb.get_database()
    return db["signals"]


def get_event_logs_collection():
    """Get the event_logs collection"""
    db = mongodb.get_database()
    return db["event_logs"]


def setup_predictions_collection(db):
    """
    Set up the predicted_demand collection with proper indexes.

    Collection Schema:
    {
        "sku": "SKU001",
        "store_id": "ST01",
        "prediction_window_days": 7,
        "predicted_demand": 240,
        "predicted_daily_avg": 34.3,
        "predicted_demand_7d": 240,
        "confidence": 0.88,
        "trend": "increasing|decreasing|stable",
        "daily_predictions": [25, 30, 35, ...],
        "model_type": "random_forest",
        "generated_at": datetime
    }
    """
    collection_name = "predicted_demand"
    collection = db[collection_name]

    # Create indexes
    indexes_created = []

    # Compound unique index on sku + store_id
    collection.create_index(
        [("sku", ASCENDING), ("store_id", ASCENDING)],
        unique=True,
        name="sku_store_idx"
    )
    indexes_created.append("sku_store_idx (compound unique)")

    # Index for high demand queries
    collection.create_index(
        [("predicted_demand_7d", DESCENDING)],
        name="predicted_demand_idx"
    )
    indexes_created.append("predicted_demand_idx")

    # Index for trend-based queries
    collection.create_index("trend", name="trend_idx")
    indexes_created.append("trend_idx")

    # Index for time-based queries
    collection.create_index(
        [("generated_at", DESCENDING)],
        name="generated_at_idx"
    )
    indexes_created.append("generated_at_idx")

    # Index for confidence filtering
    collection.create_index("confidence", name="confidence_idx")
    indexes_created.append("confidence_idx")

    logger.info(f"Predictions collection setup complete. Indexes: {indexes_created}")
    return collection


def setup_predictive_risks_collection(db):
    """
    Set up the predictive_risks collection for storing risk predictions.

    Collection Schema:
    {
        "risk_id": "RISK-XXXXXXXX",
        "risk_type": "PREDICTED_STOCKOUT|PREDICTED_DELAY|...",
        "entity_type": "store|warehouse|delivery",
        "entity_id": "string",
        "product_id": "string (optional)",
        "severity": "low|medium|high|critical",
        "probability": 0.75,
        "predicted_impact": {...},
        "mitigation_suggestions": [...],
        "created_at": datetime,
        "expires_at": datetime
    }
    """
    collection_name = "predictive_risks"
    collection = db[collection_name]

    indexes_created = []

    # Unique index on risk_id
    collection.create_index("risk_id", unique=True, name="risk_id_idx")
    indexes_created.append("risk_id_idx (unique)")

    # Compound index for active risks by type
    collection.create_index(
        [("risk_type", ASCENDING), ("severity", DESCENDING), ("probability", DESCENDING)],
        name="risk_lookup_idx"
    )
    indexes_created.append("risk_lookup_idx")

    # Index for entity lookups
    collection.create_index(
        [("entity_type", ASCENDING), ("entity_id", ASCENDING)],
        name="entity_risk_idx"
    )
    indexes_created.append("entity_risk_idx")

    # Index for product-specific risks
    collection.create_index("product_id", name="product_risk_idx")
    indexes_created.append("product_risk_idx")

    # TTL index to auto-expire old predictions after 7 days
    collection.create_index(
        "expires_at",
        name="risk_ttl_idx",
        expireAfterSeconds=0  # Expire at specified time
    )
    indexes_created.append("risk_ttl_idx (TTL)")

    # Index for high-probability risks
    collection.create_index(
        [("probability", DESCENDING), ("severity", DESCENDING)],
        name="high_risk_idx"
    )
    indexes_created.append("high_risk_idx")

    logger.info(f"Predictive risks collection setup complete. Indexes: {indexes_created}")
    return collection


def verify_collections():
    """
    Verify that all intelligence collections exist and have proper indexes.
    Returns a status report.
    """
    db = mongodb.get_database()
    if db is None:
        return {"status": "error", "message": "Database not connected"}

    report = {
        "status": "ok",
        "collections": {}
    }

    # Check signals collection
    signals_indexes = list(db.signals.list_indexes())
    report["collections"]["signals"] = {
        "exists": "signals" in db.list_collection_names(),
        "index_count": len(signals_indexes),
        "indexes": [idx["name"] for idx in signals_indexes]
    }

    # Check event_logs collection
    event_logs_indexes = list(db.event_logs.list_indexes())
    report["collections"]["event_logs"] = {
        "exists": "event_logs" in db.list_collection_names(),
        "index_count": len(event_logs_indexes),
        "indexes": [idx["name"] for idx in event_logs_indexes]
    }

    # Check predicted_demand collection
    if "predicted_demand" in db.list_collection_names():
        pred_indexes = list(db.predicted_demand.list_indexes())
        report["collections"]["predicted_demand"] = {
            "exists": True,
            "index_count": len(pred_indexes),
            "indexes": [idx["name"] for idx in pred_indexes]
        }

    # Check predictive_risks collection
    if "predictive_risks" in db.list_collection_names():
        risk_indexes = list(db.predictive_risks.list_indexes())
        report["collections"]["predictive_risks"] = {
            "exists": True,
            "index_count": len(risk_indexes),
            "indexes": [idx["name"] for idx in risk_indexes]
        }

    return report


def setup_locations_collection(db):
    """
    Set up the locations collection with proper indexes.

    Collection Schema:
    {
        "city": "Mumbai",
        "state": "Maharashtra",
        "country": "India",
        "lat": 19.0760,
        "lng": 72.8777
    }
    """
    collection_name = "locations"
    collection = db[collection_name]

    # Create indexes
    indexes_created = []

    # Unique index on city
    collection.create_index("city", unique=True)
    indexes_created.append("city (unique)")

    # Index for coordinate queries
    collection.create_index(
        [("lat", ASCENDING), ("lng", ASCENDING)],
        name="coordinates_idx"
    )
    indexes_created.append("coordinates_idx")

    logger.info(f"Locations collection setup complete. Indexes: {indexes_created}")
    return collection


def setup_transactions_collection(db):
    """
    Set up the transactions collection with proper indexes.

    Collection Schema:
    {
        "transaction_id": "TXNXXXXXXXX",
        "type": "sale|restock|transfer",
        "sku": "string",
        "quantity": int,
        "location_id": "string",
        "location_type": "warehouse|store",
        "order_id": "string (optional)",
        "customer_id": "string (optional)",
        "supplier_id": "string (optional)",
        "transfer_to": "string (optional)",
        "timestamp": datetime,
        "status": "completed|cancelled|failed"
    }
    """
    collection_name = "transactions"
    collection = db[collection_name]

    # Create indexes
    indexes_created = []

    # Unique index on transaction_id
    collection.create_index("transaction_id", unique=True)
    indexes_created.append("transaction_id (unique)")

    # Index for time-based queries
    collection.create_index(
        [("timestamp", DESCENDING)],
        name="timestamp_idx"
    )
    indexes_created.append("timestamp_idx")

    # Index for SKU lookups
    collection.create_index("sku", name="sku_idx")
    indexes_created.append("sku_idx")

    # Index for location lookups
    collection.create_index("location_id", name="location_id_idx")
    indexes_created.append("location_id_idx")

    # Index for transaction type queries
    collection.create_index("type", name="type_idx")
    indexes_created.append("type_idx")

    # Compound index for filtering by SKU and timestamp
    collection.create_index(
        [("sku", ASCENDING), ("timestamp", DESCENDING)],
        name="sku_timestamp_idx"
    )
    indexes_created.append("sku_timestamp_idx")

    # Compound index for filtering by location and timestamp
    collection.create_index(
        [("location_id", ASCENDING), ("timestamp", DESCENDING)],
        name="location_timestamp_idx"
    )
    indexes_created.append("location_timestamp_idx")

    # Index for order lookups
    collection.create_index("order_id", name="order_id_idx")
    indexes_created.append("order_id_idx")

    logger.info(f"Transactions collection setup complete. Indexes: {indexes_created}")
    return collection
