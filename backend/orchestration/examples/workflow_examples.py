"""
Orchestration Layer - Example Usage & Integration Guide

This file demonstrates how to use the orchestration layer for
autonomous supply chain management.
"""


async def example_stockout_mitigation():
    """
    Example: Automated stockout mitigation workflow

    This shows how the system handles a predicted stockout signal
    by automatically coordinating inventory transfers and replenishment.
    """

    # Simulate a predicted stockout signal from the sensing layer
    signal = {
        "signal_id": "SIG-20240115-001",
        "type": "PREDICTED_STOCKOUT",
        "severity": "high",
        "entity_type": "store",
        "entity_id": "ST001",
        "product_id": "SKU-APPLE-001",
        "details": {
            "sku": "SKU-APPLE-001",
            "product_name": "Organic Apples",
            "current_stock": 15,
            "predicted_daily_demand": 8.5,
            "days_remaining": 1.8,
            "stockout_date": "2024-01-17"
        }
    }

    # Process signal through orchestrator
    from orchestration.engine.orchestrator_service import orchestrator_service

    result = await orchestrator_service.process_signal(signal)

    """
    Expected Flow:
    1. Context Aggregation:
       - Fetch inventory levels across all warehouses
       - Get demand predictions for next 7 days
       - Check delivery ETAs
       - Analyze warehouse utilization

    2. Workflow Planning:
       - Step 1: Check nearby warehouses for stock transfer
       - Step 2: Create urgent replenishment order
       - Step 3: Reprioritize pending deliveries

    3. Policy Validation:
       - Verify transfer quantity < 500 units (auto-approve)
       - Check destination warehouse utilization < 95%
       - Ensure safety stock maintained

    4. Execution:
       - Transfer 50 units from WH002 (Mumbai) to ST001
       - Create replenishment order for 200 units
       - Update delivery priorities to "high"

    5. Monitoring & Completion:
       - Track transfer completion
       - Verify order creation
       - Generate audit trail
    """

    print(f"Workflow Created: {result['workflow_id']}")
    print(f"Status: {result['status']}")
    print(f"Steps Planned: {result.get('steps_count', 0)}")


async def example_approval_workflow():
    """
    Example: Workflow requiring human approval

    This demonstrates the approval framework for high-risk operations.
    """

    # Large inventory transfer signal
    signal = {
        "signal_id": "SIG-20240115-002",
        "type": "INVENTORY_REBALANCE",
        "severity": "medium",
        "entity_type": "warehouse",
        "entity_id": "WH001",
        "details": {
            "sku": "SKU-LAPTOP-001",
            "transfer_quantity": 750,  # Exceeds 500 unit threshold
            "from_warehouse": "WH001",
            "to_warehouse": "WH003",
            "reason": "Over-utilization detected"
        }
    }

    from orchestration.engine.orchestrator_service import orchestrator_service

    result = await orchestrator_service.process_signal(signal)

    """
    Expected Flow:
    1. Policy Engine detects quantity > 500 units
    2. Approval request created with:
       - Required role: supply_chain_director
       - Expires in: 4 hours (HIGH priority)
       - Risk level: HIGH

    3. Workflow waits in WAITING_APPROVAL state
    4. Notification sent to approval queue
    """

    if result.get('approval_id'):
        print(f"Approval Required: {result['approval_id']}")
        print(f"Required Role: {result['required_role']}")
        print(f"Expires At: {result['expires_at']}")


async def example_event_driven_orchestration():
    """
    Example: Event-driven orchestration triggers

    Shows how the system responds to operational events automatically.
    """

    from orchestration.engine.orchestrator_service import orchestrator_service

    events = [
        # Event 1: New signal created
        {
            "event_type": "signal_created",
            "event_data": {
                "signal": {
                    "signal_id": "SIG-EVT-001",
                    "type": "DELIVERY_DELAY",
                    "severity": "high",
                    "details": {
                        "delivery_id": "DEL-12345",
                        "delay_hours": 28
                    }
                }
            }
        },

        # Event 2: Stockout detected
        {
            "event_type": "stockout_detected",
            "event_data": {
                "sku": "SKU-PHONE-001",
                "warehouse_id": "WH002",
                "available_stock": 0
            }
        },

        # Event 3: Approval received
        {
            "event_type": "approval_received",
            "event_data": {
                "approval_id": "APR-20240115-001",
                "decision": "approve",
                "approved_by": "john.doe@company.com",
                "notes": "Approved - urgent customer demand"
            }
        }
    ]

    for event in events:
        result = await orchestrator_service.handle_event(
            event['event_type'],
            event['event_data']
        )
        print(f"Event {event['event_type']}: {result.get('workflow_id', 'processed')}")


async def example_failure_recovery():
    """
    Example: Automatic failure recovery

    Demonstrates how the system handles execution failures.
    """

    # Simulate a workflow with failures
    workflow_id = "WF-20240115-FAILED"

    # The execution engine would:
    # 1. Attempt step execution
    # 2. Detect failure (e.g., inventory transfer failed)
    # 3. Trigger recovery:
    #    - Retry with alternate warehouse
    #    - Or rollback completed steps
    #    - Or escalate to human operators

    """
    Recovery Strategies:

    Strategy 1: RETRY
    - Step failed: Inventory transfer from WH001
    - System finds alternate: WH003 with stock
    - Retries transfer automatically
    - Max retries: 3

    Strategy 2: ROLLBACK
    - If retry fails, rollback:
      - Reverse completed inventory transfers
      - Cancel created orders
      - Restore original state

    Strategy 3: ESCALATE
    - If rollback fails or not possible
    - Create escalation record
    - Notify operations team
    - Provide diagnostic information
    """


async def example_llm_integration():
    """
    Example: Safe LLM-assisted orchestration

    Shows how LLMs can assist without direct execution power.
    """

    """
    LLM is ONLY used for:
    - Analyzing complex scenarios
    - Generating recommendations
    - Explaining workflow decisions
    - Providing natural language summaries

    LLM CANNOT:
    - Execute actions directly
    - Bypass policy validation
    - Modify database directly
    - Skip approval requirements

    Safe Flow:
    1. LLM analyzes signal context
    2. LLM generates action recommendations
    3. Recommendations validated against policies
    4. Policies enforce required approvals
    5. Only execution engine can invoke services
    """

    # Example LLM output (simulated)
    llm_recommendation = {
        "analysis": "Stockout predicted within 48 hours for high-demand SKU",
        "risk_level": "high",
        "recommended_actions": [
            {
                "action": "inventory_transfer",
                "from_warehouse": "WH002",
                "quantity": 100,
                "priority": "high",
                "reasoning": "WH002 has 150 units available, 30km distance"
            },
            {
                "action": "create_replenishment_order",
                "quantity": 300,
                "priority": "high",
                "reasoning": "Demand forecast indicates need for 45 units/day"
            }
        ],
        "considerations": [
            "Customer VIP status: Premium priority recommended",
            "Historical stockout impact: 15% revenue loss",
            "Alternative suppliers available: 2"
        ]
    }

    # These recommendations still go through policy validation!
    # LLM output is NOT trusted blindly


# ============================================================
# INTEGRATION WITH EXISTING SERVICES
# ============================================================

def integration_example():
    """
    Shows how orchestration integrates with existing services.
    """

    # The orchestration layer NEVER bypasses existing services:

    # Instead of:
    # db.inventory.update_one(...)  ← NEVER DO THIS

    # We do:
    """
    from services.inventory_service import InventoryService
    inventory_service = InventoryService()

    # All validation happens in the service
    result = inventory_service.allocate_inventory(
        warehouse_id="WH001",
        sku="SKU-001",
        quantity=50
    )
    """

    # Same for all other operations:
    # - OrderService for orders
    # - WarehouseService for warehouses
    # - DeliveryService for deliveries
    # - DecisionService for replenishment

    pass


# ============================================================
# MONITORING & OBSERVABILITY
# ============================================================

async def monitoring_example():
    """
    Example: Monitoring orchestration operations
    """

    from orchestration.engine.orchestrator_service import orchestrator_service
    from orchestration.monitoring.execution_monitor import ExecutionMonitor

    # Get orchestration metrics
    metrics = await orchestrator_service.get_orchestration_metrics()

    print(f"""
    Orchestration Metrics:
    ├─ Total Workflows: {metrics['total_workflows']}
    ├─ Active: {metrics['active_workflows']}
    ├─ Completed: {metrics['completed_workflows']}
    ├─ Failed: {metrics['failed_workflows']}
    └─ Avg Execution Time: {metrics.get('avg_execution_time_seconds', 0):.2f}s
    """)

    # Get health status
    health = await orchestrator_service.health_check()

    print(f"""
    Health Status: {health['status']}
    ├─ Orchestrator Active: {health['orchestrator_active']}
    ├─ Services Available:
    │  ├─ Inventory: {health['services_available'].get('inventory', False)}
    │  ├─ Orders: {health['services_available'].get('orders', False)}
    │  └─ Deliveries: {health['services_available'].get('deliveries', False)}
    └─ Issues: {len(health['issues'])}
    """)


# ============================================================
# DEMONSTRATION SCRIPT
# ============================================================

async def run_demonstration():
    """
    Run complete orchestration demonstration
    """

    print("=" * 60)
    print("ORCHESTRATION LAYER DEMONSTRATION")
    print("=" * 60)

    # Start orchestrator
    from orchestration.engine.orchestrator_service import orchestrator_service
    orchestrator_service.start()

    print("\n[1] Stockout Mitigation Workflow")
    print("-" * 60)
    await example_stockout_mitigation()

    print("\n[2] Approval Workflow")
    print("-" * 60)
    await example_approval_workflow()

    print("\n[3] Event-Driven Orchestration")
    print("-" * 60)
    await example_event_driven_orchestration()

    print("\n[4] Monitoring & Observability")
    print("-" * 60)
    await monitoring_example()

    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_demonstration())
