"""
LLM Orchestrator Prompts

Contains prompt templates and builders for the LLM orchestration engine.
"""
from typing import Dict, Any


class OrchestratorPrompts:
    """Prompt templates for LLM orchestration"""

    SYSTEM_PROMPT = """You are an intelligent supply chain orchestration assistant.

Your role is to analyze supply chain data and generate actionable plans to:
- Prevent stockouts and overstock situations
- Optimize inventory distribution across warehouses
- Respond to critical signals and alerts
- Balance supply and demand across the network

You must respond with valid JSON containing:
- priority: "critical", "high", "medium", or "low"
- situation: Brief description of current state
- severity: Assessment of urgency
- actions: List of action objects with action_type, priority, and reason
- reasoning: List of strings explaining your decisions
- expected_outcome: What the actions will achieve
- risk_assessment: Potential risks of the recommended actions
- confidence: Float between 0-1 representing confidence level

Action types available:
- replenish_inventory: Move stock to a location
- rebalance_inventory: Redistribute stock across locations
- expedite_order: Prioritize an order
- delay_order: Delay an order
- no_action: System is stable, no immediate action needed

Always prioritize preventing stockouts and maintaining service levels."""

    @staticmethod
    def build_orchestration_prompt(context: Dict[str, Any], agent_outputs: Dict[str, Any]) -> str:
        """
        Build the orchestration prompt from context and agent outputs.

        Args:
            context: Aggregated context data
            agent_outputs: Outputs from sensing, forecasting, optimization, and execution agents

        Returns:
            Formatted prompt string
        """
        sections = []

        # Context summary
        sections.append("## Current Supply Chain State")
        sections.append("")

        # Signals
        signals = context.get("signals", {})
        sections.append(f"### Active Signals: {signals.get('total_active', 0)}")
        if signals.get("critical_count", 0) > 0:
            sections.append(f"**CRITICAL:** {signals.get('critical_count', 0)} critical signals")
        for sig in signals.get("top_signals", [])[:5]:
            sections.append(f"- {sig.get('type', 'Unknown')}: {sig.get('message', 'No details')}")
        sections.append("")

        # Inventory summary
        inv = context.get("inventory_summary", {})
        sections.append("### Inventory Status")
        sections.append(f"- Total Stock: {inv.get('total_stock', 0):,}")
        sections.append(f"- Low Stock Items: {inv.get('total_low_stock', 0)}")
        sections.append(f"- Out of Stock Items: {inv.get('total_out_of_stock', 0)}")
        sections.append("")

        # Warehouse summary
        wh = context.get("warehouse_summary", {})
        sections.append("### Warehouse Status")
        sections.append(f"- Active Warehouses: {wh.get('total_warehouses', 0)}")
        sections.append(f"- Average Utilization: {wh.get('avg_utilization_percent', 0):.1f}%")
        sections.append("")

        # Critical issues
        critical = context.get("critical_issues", [])
        if critical:
            sections.append("### Critical Issues")
            for issue in critical[:5]:
                sections.append(f"- {issue.get('type', 'Unknown')}: {issue.get('description', 'No details')}")
            sections.append("")

        # Agent outputs
        sections.append("## Agent Analysis")
        sections.append("")

        # Sensing
        sensing = agent_outputs.get("sensing", {})
        sections.append("### Sensing Agent")
        for rec in sensing.get("recommendations", [])[:3]:
            sections.append(f"- {rec}")
        sections.append("")

        # Forecasting
        forecasting = agent_outputs.get("forecasting", {})
        risks = forecasting.get("stockout_risks", [])
        sections.append("### Forecasting Agent")
        sections.append(f"- Stockout Risks Identified: {len(risks)}")
        for risk in risks[:3]:
            sections.append(f"  - {risk.get('sku', 'Unknown')}: {risk.get('probability', 0):.0%} probability")
        sections.append("")

        # Optimization
        optimization = agent_outputs.get("optimization", {})
        sections.append("### Optimization Agent")
        opps = optimization.get("optimization_plan", [])
        sections.append(f"- Optimization Opportunities: {len(opps)}")
        for opp in opps[:3]:
            sections.append(f"  - {opp.get('type', 'Unknown')}: Save ${opp.get('potential_savings', 0):,.0f}")
        sections.append("")

        # Execution
        execution = agent_outputs.get("execution", {})
        sections.append("### Execution Agent")
        capacity = execution.get("capacity", {})
        sections.append(f"- Can Execute: {capacity.get('can_execute', True)}")
        sections.append("")

        # Request
        sections.append("## Requested Action")
        sections.append("")
        sections.append("Based on the above context and agent analyses, generate an orchestration plan.")
        sections.append("Return ONLY valid JSON with the structure specified in the system prompt.")
        sections.append("")
        sections.append("```json")

        return "\n".join(sections)


def build_orchestration_prompt(context: Dict[str, Any], agent_outputs: Dict[str, Any]) -> str:
    """
    Convenience function to build orchestration prompt.

    Args:
        context: Aggregated context data
        agent_outputs: Outputs from all agents

    Returns:
        Formatted prompt string
    """
    return OrchestratorPrompts.build_orchestration_prompt(context, agent_outputs)
