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
        
        logger.info("Intelligence Layer collections setup complete")
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
    
    return report
