"""
LLM Orchestrator Service - Main orchestration engine with LLM reasoning

Coordinates all agents, validates decisions, and manages execution.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from db.connection import mongodb
from services.context_service import context_service
from services.validation_service import validation_service
from orchestration.agents import (
    sensing_agent, forecasting_agent, optimization_agent, execution_agent
)
from orchestration.prompts.orchestrator_prompt import OrchestratorPrompts
from orchestration.schemas.action_schema import (
    OrchestrationPlan, ActionSchema, Priority, ActionType
)
import logging
import json
import uuid
import re

logger = logging.getLogger(__name__)


class LLMOrchestratorService:
    """
    Main LLM-powered orchestration service.

    Coordinates:
    - Context aggregation
    - Multi-agent analysis
    - LLM reasoning
    - Decision validation
    - Action execution
    - History tracking
    """

    def __init__(self):
        self.model = None
        self.model_name = "gpt-4"
        self.temperature = 0.1
        self.max_tokens = 2000

    @property
    def db(self):
        return mongodb.get_database()

    def generate_plan(
        self,
        context: Optional[Dict[str, Any]] = None,
        signal: Optional[Dict[str, Any]] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Generate an orchestration plan using LLM reasoning.

        Args:
            context: Optional pre-aggregated context
            signal: Optional signal to focus on
            dry_run: If True, don't execute actions

        Returns:
            Orchestration plan with decisions
        """
        plan_id = f"PLAN-{uuid.uuid4().hex[:8].upper()}"
        decision_id = f"DEC-{uuid.uuid4().hex[:8].upper()}"

        logger.info(f"Generating orchestration plan {plan_id}")

        try:
            # Step 1: Aggregate context
            if context is None:
                if signal:
                    context = context_service.aggregate_context_for_signal(signal)
                else:
                    context = context_service.aggregate_context()

            # Step 2: Run agent analyses
            agent_outputs = self._run_agents(context)

            # Step 3: Generate LLM decision
            llm_response = self._call_llm(context, agent_outputs)

            # Step 4: Parse LLM response
            parsed_plan = self._parse_llm_response(llm_response)

            if not parsed_plan:
                return {
                    "success": False,
                    "plan_id": plan_id,
                    "error": "Failed to parse LLM response",
                    "raw_response": llm_response
                }

            # Step 5: Validate actions
            validation_results = validation_service.validate_plan(parsed_plan.get("actions", []))

            # Step 6: Build decision
            decision = {
                "decision_id": decision_id,
                "plan_id": plan_id,
                "timestamp": datetime.utcnow().isoformat(),
                "context_summary": self._summarize_context(context),
                "llm_plan": parsed_plan,
                "agent_outputs": self._summarize_agent_outputs(agent_outputs),
                "validation_results": [v.dict() for v in validation_results],
                "can_auto_execute": all(v.valid for v in validation_results),
                "dry_run": dry_run
            }

            # Step 7: Store in history
            self._store_decision(decision)

            # Step 8: Execute if not dry run
            if not dry_run and decision["can_auto_execute"]:
                execution_results = self._execute_actions(parsed_plan.get("actions", []))
                decision["execution_results"] = execution_results

            return {
                "success": True,
                "plan_id": plan_id,
                "decision": decision
            }

        except Exception as e:
            logger.error(f"Error generating plan: {e}")
            return {
                "success": False,
                "plan_id": plan_id,
                "error": str(e)
            }

    def _run_agents(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run all agent analyses"""
        return {
            "sensing": sensing_agent.process(context),
            "forecasting": forecasting_agent.process(context),
            "optimization": optimization_agent.process(context),
            "execution": execution_agent.process(context)
        }

    def _call_llm(self, context: Dict[str, Any], agent_outputs: Dict[str, Any]) -> str:
        """
        Call LLM with orchestration prompt.

        Supports multiple providers: OpenAI, Anthropic, or mock for testing.
        """
        prompt = OrchestratorPrompts.build_orchestration_prompt(context, agent_outputs)

        # Check for API keys
        import os

        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")

        if openai_key:
            return self._call_openai(prompt, openai_key)
        elif anthropic_key:
            return self._call_anthropic(prompt, anthropic_key)
        else:
            # Return mock response for testing
            logger.warning("No LLM API key found - returning mock response")
            return self._get_mock_response(context)

    def _call_openai(self, prompt: str, api_key: str) -> str:
        """Call OpenAI API"""
        try:
            import openai

            client = openai.OpenAI(api_key=api_key)

            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": OrchestratorPrompts.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return self._get_error_response(str(e))

    def _call_anthropic(self, prompt: str, api_key: str) -> str:
        """Call Anthropic API"""
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=api_key)

            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=self.max_tokens,
                system=OrchestratorPrompts.SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return self._get_error_response(str(e))

    def _parse_llm_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse LLM response into structured plan.

        Handles malformed JSON and extracts valid structure.
        """
        try:
            # Try direct JSON parse
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from the response
        try:
            # Find JSON-like content
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except (json.JSONDecodeError, AttributeError):
            pass

        # Try to fix common issues
        try:
            # Remove markdown code blocks
            cleaned = re.sub(r'```json\s*', '', response)
            cleaned = re.sub(r'```\s*', '', cleaned)
            return json.loads(cleaned)
        except:
            pass

        logger.error("Failed to parse LLM response as JSON")
        return None

    def _get_mock_response(self, context: Dict[str, Any]) -> str:
        """Generate mock LLM response based on context"""
        # Analyze context to generate relevant mock response
        critical_issues = context.get("critical_issues", [])
        signals = context.get("signals", {})
        inventory = context.get("inventory_summary", {})

        actions = []
        reasoning = []

        # Generate actions based on context
        if signals.get("critical_count", 0) > 0:
            top_signals = signals.get("top_signals", [])
            for sig in top_signals[:2]:
                if sig.get("type") == "STOCKOUT":
                    actions.append({
                        "action_type": "replenish_inventory",
                        "priority": "critical",
                        "sku": sig.get("product_id", "SKU001"),
                        "warehouse_id": sig.get("entity_id", "WH001"),
                        "quantity": 100,
                        "reason": "Addressing stockout condition"
                    })
                    reasoning.append(f"Stockout detected for {sig.get('product_id')} at {sig.get('entity_id')}")

        if inventory.get("total_low_stock", 0) > 5:
            actions.append({
                "action_type": "rebalance_inventory",
                "priority": "high",
                "reason": "Multiple low stock items require inventory rebalancing"
            })
            reasoning.append(f"{inventory.get('total_low_stock')} items with low stock")

        if not actions:
            actions.append({
                "action_type": "no_action",
                "priority": "low",
                "reason": "System operating within normal parameters"
            })
            reasoning.append("No critical issues detected")

        mock_plan = {
            "priority": "high" if critical_issues else "medium",
            "situation": f"{signals.get('total_active', 0)} active signals, {inventory.get('total_low_stock', 0)} low stock items",
            "severity": "high" if critical_issues else "medium",
            "actions": actions,
            "reasoning": reasoning or ["System analysis complete"],
            "expected_outcome": "Improved inventory levels and reduced signal count",
            "risk_assessment": "Low risk - standard restocking operations",
            "confidence": 0.85
        }

        return json.dumps(mock_plan)

    def _get_error_response(self, error: str) -> str:
        """Generate error response"""
        return json.dumps({
            "priority": "low",
            "situation": f"LLM API error: {error}",
            "severity": "medium",
            "actions": [{
                "action_type": "no_action",
                "priority": "low",
                "reason": "Unable to generate plan due to API error"
            }],
            "reasoning": ["LLM API call failed"],
            "expected_outcome": "Manual review required",
            "risk_assessment": "Unable to assess",
            "confidence": 0.0
        })

    def _summarize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of context for storage"""
        return {
            "signals_count": context.get("signals", {}).get("total_active", 0),
            "low_stock_count": context.get("inventory_summary", {}).get("total_low_stock", 0),
            "warehouse_utilization": context.get("warehouse_summary", {}).get("avg_utilization_percent", 0),
            "delayed_deliveries": context.get("delivery_summary", {}).get("delayed_count", 0),
            "critical_issues_count": len(context.get("critical_issues", []))
        }

    def _summarize_agent_outputs(self, outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize agent outputs"""
        return {
            "sensing_recommendations": outputs.get("sensing", {}).get("recommendations", [])[:3],
            "forecasting_risks": len(outputs.get("forecasting", {}).get("stockout_risks", [])),
            "optimization_opportunities": len(outputs.get("optimization", {}).get("optimization_plan", [])),
            "execution_capability": outputs.get("execution", {}).get("capacity", {}).get("can_execute", True)
        }

    def _store_decision(self, decision: Dict[str, Any]) -> None:
        """Store decision in orchestration history"""
        try:
            history_record = {
                "history_id": f"HIST-{uuid.uuid4().hex[:8].upper()}",
                "decision_id": decision["decision_id"],
                "plan_id": decision["plan_id"],
                "timestamp": decision["timestamp"],
                "context_summary": decision["context_summary"],
                "llm_plan": decision["llm_plan"],
                "validation_results": decision["validation_results"],
                "can_auto_execute": decision["can_auto_execute"],
                "agent_outputs": decision["agent_outputs"],
                "status": "pending"
            }

            self.db.orchestration_history.insert_one(history_record)
            logger.info(f"Stored decision {decision['decision_id']} in history")

        except Exception as e:
            logger.error(f"Error storing decision: {e}")

    def _execute_actions(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute validated actions"""
        results = []

        for action in actions:
            result = execution_agent.execute_action(action, dry_run=False)
            results.append(result)

            # Update history
            if result.get("status") == "success":
                logger.info(f"Successfully executed action {action.get('action_type')}")

        return results

    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get orchestration history"""
        try:
            history = list(self.db.orchestration_history.find(
                {},
                {"_id": 0}
            ).sort("timestamp", -1).limit(limit))

            return history

        except Exception as e:
            logger.error(f"Error getting history: {e}")
            return []

    def get_decision(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """Get specific decision by ID"""
        try:
            decision = self.db.orchestration_history.find_one(
                {"decision_id": decision_id},
                {"_id": 0}
            )
            return decision

        except Exception as e:
            logger.error(f"Error getting decision: {e}")
            return None

    def explain_decision(self, decision_id: str) -> Dict[str, Any]:
        """
        Generate explanation for a decision.

        Args:
            decision_id: Decision to explain

        Returns:
            Explanation with reasoning
        """
        decision = self.get_decision(decision_id)

        if not decision:
            return {"error": f"Decision {decision_id} not found"}

        plan = decision.get("llm_plan", {})

        explanation = {
            "decision_id": decision_id,
            "timestamp": decision.get("timestamp"),
            "situation": plan.get("situation"),
            "severity": plan.get("severity"),
            "reasoning": plan.get("reasoning", []),
            "expected_outcome": plan.get("expected_outcome"),
            "risk_assessment": plan.get("risk_assessment"),
            "confidence": plan.get("confidence"),
            "context_at_decision": decision.get("context_summary"),
            "actions_taken": [
                {
                    "action": a.get("action_type"),
                    "reason": a.get("reason"),
                    "priority": a.get("priority")
                }
                for a in plan.get("actions", [])
            ],
            "validation_status": "passed" if decision.get("can_auto_execute") else "requires_review",
            "agent_insights": decision.get("agent_outputs", {})
        }

        return explanation

    def get_metrics(self) -> Dict[str, Any]:
        """Get orchestration metrics"""
        try:
            total_decisions = self.db.orchestration_history.count_documents({})

            # Count by status
            pipeline = [
                {"$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }}
            ]

            status_counts = {
                item["_id"]: item["count"]
                for item in self.db.orchestration_history.aggregate(pipeline)
            }

            # Recent decisions
            recent = list(self.db.orchestration_history.find(
                {},
                {"_id": 0, "decision_id": 1, "timestamp": 1, "status": 1}
            ).sort("timestamp", -1).limit(5))

            return {
                "total_decisions": total_decisions,
                "status_breakdown": status_counts,
                "recent_decisions": recent,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}

    def setup_collections(self) -> None:
        """Setup orchestration history collection"""
        try:
            # Create collection if not exists
            if "orchestration_history" not in self.db.list_collection_names():
                self.db.create_collection("orchestration_history")

            # Create indexes
            self.db.orchestration_history.create_index("history_id", unique=True)
            self.db.orchestration_history.create_index("decision_id", unique=True)
            self.db.orchestration_history.create_index("plan_id")
            self.db.orchestration_history.create_index("timestamp")

            logger.info("Orchestration history collection initialized")

        except Exception as e:
            logger.error(f"Error setting up collections: {e}")


# Global instance
llm_orchestrator_service = LLMOrchestratorService()
