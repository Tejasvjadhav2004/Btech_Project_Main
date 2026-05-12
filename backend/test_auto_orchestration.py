"""
Test Script for Automatic Orchestration

This script demonstrates the auto-processing feature where signals
automatically trigger orchestration workflows.
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_auto_orchestration():
    """Test automatic signal processing through orchestration"""

    print("\n" + "="*60)
    print("TESTING AUTOMATIC ORCHESTRATION")
    print("="*60 + "\n")

    # Step 1: Check auto processor status
    print("Step 1: Checking Auto Processor Status...")
    response = requests.get(f"{BASE_URL}/api/orchestration/auto-processor/status")
    status = response.json()
    print(f"Auto Processor Active: {status.get('active')}")
    print(f"Auto-process severities: {status.get('auto_process_severities')}")
    print(f"Orchestrator Active: {status.get('orchestrator_active')}")
    print()

    # Step 2: Create a critical signal
    print("Step 2: Creating a CRITICAL stockout signal...")
    signal_data = {
        "signal_type": "STOCKOUT",
        "entity_type": "store",
        "entity_id": "ST001",
        "product_id": "SKU-001",
        "severity": "critical",
        "message": "Test stockout signal for auto-orchestration",
        "details": {
            "current_stock": 0,
            "product_name": "Test Product"
        },
        "source": "test_script"
    }

    response = requests.post(
        f"{BASE_URL}/api/signals/",
        json=signal_data
    )

    if response.status_code == 200:
        signal = response.json()
        signal_id = signal.get("signal_id")
        print(f"✓ Signal created: {signal_id}")
        print(f"  Type: {signal.get('type')}")
        print(f"  Severity: {signal.get('severity')}")
        print(f"  Status: {signal.get('status')}")
    else:
        print(f"✗ Failed to create signal: {response.text}")
        return
    print()

    # Step 3: Wait for auto-processing
    print("Step 3: Waiting for auto-processing (30 seconds)...")
    time.sleep(30)
    print()

    # Step 4: Check if workflow was created
    print("Step 4: Checking workflows...")
    response = requests.get(f"{BASE_URL}/api/orchestration/active")
    workflows_data = response.json()
    workflows = workflows_data.get("workflows", [])

    print(f"Total active workflows: {len(workflows)}")

    # Find workflow for our signal
    matching_workflow = None
    for wf in workflows:
        if wf.get("trigger_signal_id") == signal_id or signal_id in str(wf):
            matching_workflow = wf
            break

    if matching_workflow:
        print(f"\n✓ WORKFLOW CREATED AUTOMATICALLY!")
        print(f"  Workflow ID: {matching_workflow.get('workflow_id')}")
        print(f"  Type: {matching_workflow.get('workflow_type')}")
        print(f"  Status: {matching_workflow.get('status')}")
        print(f"  Priority: {matching_workflow.get('priority')}")
        print(f"  Steps: {len(matching_workflow.get('steps', []))}")
    else:
        print("\n✗ No workflow found for signal")
        print("Recent workflows:")
        for wf in workflows[:3]:
            print(f"  - {wf.get('workflow_id')}: {wf.get('status')}")
    print()

    # Step 5: Check signal status
    print("Step 5: Checking signal status...")
    response = requests.get(f"{BASE_URL}/api/signals/{signal_id}")
    updated_signal = response.json()

    print(f"Signal Status: {updated_signal.get('status')}")
    if updated_signal.get('auto_resolved'):
        print(f"✓ Signal was AUTO-RESOLVED!")
        print(f"Resolution: {updated_signal.get('resolution_note')}")
    elif updated_signal.get('status') == 'acknowledged':
        print(f"Signal acknowledged (workflow pending approval)")
    print()

    # Step 6: Check pending approvals
    print("Step 6: Checking pending approvals...")
    response = requests.get(f"{BASE_URL}/api/orchestration/approvals")
    approvals_data = response.json()
    approvals = approvals_data.get("approvals", [])

    print(f"Pending approvals: {len(approvals)}")

    if approvals:
        print("\nPending Approval:")
        approval = approvals[0]
        print(f"  Workflow: {approval.get('workflow_id')}")
        print(f"  Risk Level: {approval.get('risk_level')}")
        print(f"  Required Role: {approval.get('required_role')}")
        print(f"  Action: {approval.get('action_summary')}")

        # Approve the workflow
        print("\nApproving workflow...")
        response = requests.post(
            f"{BASE_URL}/api/orchestration/approve?workflow_id={approval.get('workflow_id')}",
            json={
                "approved_by": "test_script",
                "notes": "Approved for testing"
            }
        )

        if response.status_code == 200:
            print("✓ Workflow approved and executing!")

            # Wait for execution
            print("\nWaiting for execution (5 seconds)...")
            time.sleep(5)

            # Check workflow status
            wf_id = approval.get('workflow_id')
            response = requests.get(f"{BASE_URL}/api/orchestration/workflows/{wf_id}")
            workflow = response.json().get('workflow')

            print(f"\nWorkflow Status after approval:")
            print(f"  Status: {workflow.get('status')}")
            print(f"  Steps Executed: {len([s for s in workflow.get('steps', []) if s.get('status') == 'completed'])}")
            print(f"  Execution Time: {workflow.get('execution_time_seconds', 0):.2f}s")
        else:
            print(f"✗ Failed to approve: {response.text}")

    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60 + "\n")

    # Summary
    print("SUMMARY:")
    print(f"  Signal Created: {signal_id}")
    if matching_workflow:
        print(f"  Workflow Created: {matching_workflow.get('workflow_id')}")
        print(f"  Auto-Processing: ✓ WORKING")
    else:
        print(f"  Auto-Processing: ✗ NOT WORKING")


if __name__ == "__main__":
    try:
        test_auto_orchestration()
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure the backend server is running:")
        print("  cd backend")
        print("  python -m api.main")
