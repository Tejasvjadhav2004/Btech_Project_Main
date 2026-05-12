"""
Orchestration Collections Setup

MongoDB collection definitions for workflow management.
"""
from pymongo import ASCENDING, DESCENDING
from db.connection import mongodb
import logging

logger = logging.getLogger(__name__)


def setup_orchestration_collections():
    """
    Set up MongoDB collections for orchestration layer.

    Collections:
    - orchestration_workflows: Active and historical workflows
    - workflow_logs: Detailed execution logs
    - action_audit_logs: Audit trail for all actions
    - approval_requests: Approval management
    """
    db = mongodb.get_database()
    if db is None:
        logger.error("Database connection not available for orchestration setup")
        return False

    try:
        _setup_workflows_collection(db)
        _setup_workflow_logs_collection(db)
        _setup_action_audit_collection(db)
        _setup_approval_requests_collection(db)

        logger.info("Orchestration collections setup complete")
        return True
    except Exception as e:
        logger.error(f"Error setting up orchestration collections: {e}")
        return False


def _setup_workflows_collection(db):
    """Setup orchestration_workflows collection"""
    collection = db["orchestration_workflows"]

    indexes = [
        ("workflow_id", ASCENDING, True),  # Unique
        ("status", ASCENDING, False),
        ("priority", DESCENDING, False),
        ("workflow_type", ASCENDING, False),
        ("trigger_signal_id", ASCENDING, False),
        ("created_at", DESCENDING, False),
        ("updated_at", DESCENDING, False),
    ]

    for field, direction, unique in indexes:
        collection.create_index([(field, direction)], unique=unique)

    # Compound index for active workflows
    collection.create_index(
        [("status", ASCENDING), ("priority", DESCENDING)],
        name="active_workflows_idx"
    )

    logger.info("Orchestration workflows collection configured")


def _setup_workflow_logs_collection(db):
    """Setup workflow_logs collection"""
    collection = db["workflow_logs"]

    indexes = [
        ("log_id", ASCENDING, True),  # Unique
        ("workflow_id", ASCENDING, False),
        ("step_id", ASCENDING, False),
        ("event_type", ASCENDING, False),
        ("timestamp", DESCENDING, False),
    ]

    for field, direction, unique in indexes:
        collection.create_index([(field, direction)], unique=unique)

    # Compound index for workflow history
    collection.create_index(
        [("workflow_id", ASCENDING), ("timestamp", DESCENDING)],
        name="workflow_history_idx"
    )

    # TTL index - expire logs after 90 days
    collection.create_index(
        "timestamp",
        name="ttl_idx",
        expireAfterSeconds=90 * 24 * 60 * 60
    )

    logger.info("Workflow logs collection configured")


def _setup_action_audit_collection(db):
    """Setup action_audit_logs collection"""
    collection = db["action_audit_logs"]

    indexes = [
        ("action_id", ASCENDING, True),  # Unique
        ("workflow_id", ASCENDING, False),
        ("action_type", ASCENDING, False),
        ("timestamp", DESCENDING, False),
        ("sku", ASCENDING, False),
        ("warehouse_id", ASCENDING, False),
    ]

    for field, direction, unique in indexes:
        collection.create_index([(field, direction)], unique=unique)

    # TTL index - expire after 365 days
    collection.create_index(
        "timestamp",
        name="audit_ttl_idx",
        expireAfterSeconds=365 * 24 * 60 * 60
    )

    logger.info("Action audit logs collection configured")


def _setup_approval_requests_collection(db):
    """Setup approval_requests collection"""
    collection = db["approval_requests"]

    indexes = [
        ("approval_id", ASCENDING, True),  # Unique
        ("workflow_id", ASCENDING, False),
        ("status", ASCENDING, False),
        ("required_role", ASCENDING, False),
        ("created_at", DESCENDING, False),
        ("expires_at", ASCENDING, False),
    ]

    for field, direction, unique in indexes:
        collection.create_index([(field, direction)], unique=unique)

    # Index for pending approvals
    collection.create_index(
        [("status", ASCENDING), ("expires_at", ASCENDING)],
        name="pending_approvals_idx"
    )

    # TTL index on expires_at
    collection.create_index(
        "expires_at",
        name="approval_ttl_idx",
        expireAfterSeconds=0
    )

    logger.info("Approval requests collection configured")


def get_workflows_collection():
    """Get orchestration_workflows collection"""
    db = mongodb.get_database()
    return db["orchestration_workflows"]


def get_workflow_logs_collection():
    """Get workflow_logs collection"""
    db = mongodb.get_database()
    return db["workflow_logs"]


def get_audit_logs_collection():
    """Get action_audit_logs collection"""
    db = mongodb.get_database()
    return db["action_audit_logs"]


def get_approvals_collection():
    """Get approval_requests collection"""
    db = mongodb.get_database()
    return db["approval_requests"]
