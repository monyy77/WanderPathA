"""
WanderPathA - Console Demo / Main Entry Point

This is the console-facing entry point for the EXISTING WanderPathA project.
It intentionally does not import the website/API layer.

Project routes used here:
    Memory & RAG -> agent.agent.run_agent
    Flight       -> state_graph.graphs.flight_rebooking
    Planning     -> planning.planning_agent
    Refund       -> state_graph.refundGraph.refund_graph
    VIP          -> state_graph.graphs.vip_trip_customization

Important:
    Project imports are explicit below. We do NOT dynamically import every
    file in tools/, because tools/utilties.py eagerly creates TavilySearch
    and therefore crashes at startup when TAVILY_API_KEY is absent.
"""

from __future__ import annotations

import asyncio
import sys
import time
import uuid
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Project root bootstrap
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Existing project tools
# ---------------------------------------------------------------------------

class ConsoleToolClient:
    """Adapter exposing the project's existing LangChain tools to agents."""

    def __init__(self, tools: dict[str, Any]):
        self._tools = tools

    async def get_tools(self) -> list[Any]:
        return list(self._tools.values())


def build_project_tool_registry() -> dict[str, Any]:
    """
    Explicitly import the tools that actually exist in this ZIP.

    Notice that tools/utilties.py is intentionally NOT imported here.
    It eagerly constructs TavilySearchResults and requires TAVILY_API_KEY.
    """
    from tools.booking_tools import (
        get_nearby_airports,
        get_flight_options,
        get_bookings_by_flight,
    )
    from tools.customer_tools import (
        get_customer_profile,
        get_booking_history,
        UpdateCustomerProfile,
    )
    from tools.finance_and_decision_tools import (
        CalculateTripCost,
        CheckRefundEligibility,
        CalculateRefundAmount,
        ProcessRefund,
        CalculateCompensation,
        IssueTravelVoucher,
        CompareRebookingCost,
    )
    from tools.travel_status_tools import (
        get_flight_status,
        get_delay_duration,
        check_disruption_reason,
        get_weather,
        check_airport_status,
        check_connection_risk,
        get_estimated_departure,
        get_estimated_arrival,
        check_alternative_transport,
        get_disruption_severity,
    )
    from tools.escalation_tools import (
        escalate_to_human,
        create_support_ticket,
        schedule_agent_callback,
        notify_supervisor,
        log_escalation,
    )

    project_tools = [
        get_nearby_airports,
        get_flight_options,
        get_bookings_by_flight,
        get_customer_profile,
        get_booking_history,
        UpdateCustomerProfile,
        CalculateTripCost,
        CheckRefundEligibility,
        CalculateRefundAmount,
        ProcessRefund,
        CalculateCompensation,
        IssueTravelVoucher,
        CompareRebookingCost,
        get_flight_status,
        get_delay_duration,
        check_disruption_reason,
        get_weather,
        check_airport_status,
        check_connection_risk,
        get_estimated_departure,
        get_estimated_arrival,
        check_alternative_transport,
        get_disruption_severity,
        escalate_to_human,
        create_support_ticket,
        schedule_agent_callback,
        notify_supervisor,
        log_escalation,
    ]

    return {tool.name: tool for tool in project_tools}


# Do NOT build this at module import time.
# The menu should open even when an optional dependency/API key is missing.
_LOCAL_CLIENT: ConsoleToolClient | None = None


def get_local_client() -> ConsoleToolClient:
    global _LOCAL_CLIENT
    if _LOCAL_CLIENT is None:
        _LOCAL_CLIENT = ConsoleToolClient(build_project_tool_registry())
    return _LOCAL_CLIENT


# ---------------------------------------------------------------------------
# Console UI
# ---------------------------------------------------------------------------


def banner() -> None:
    print("\n" + "=" * 72)
    print("                    WANDERPATH TRAVEL")
    print("                       CONSOLE DEMO")
    print("=" * 72)
    print("Console entry point for the existing agents/graphs")
    print("Website / FastAPI endpoints are NOT used here.")


def pause() -> None:
    input("\nPress Enter to return to the main menu...")


def ask(prompt: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default is not None else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value if value else (default or "")


def ask_int(prompt: str, default: int) -> int:
    while True:
        value = ask(prompt, str(default))
        try:
            return int(value)
        except ValueError:
            print("Please enter a valid integer.")


def ask_yes_no(prompt: str, default: bool = True) -> bool:
    default_value = "y" if default else "n"
    while True:
        value = ask(f"{prompt} (y/n)", default_value).lower()
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("Please answer y or n.")


def show_result(result: Any) -> None:
    print("\n" + "-" * 72)
    print("RESULT")
    print("-" * 72)
    if isinstance(result, dict):
        for key, value in result.items():
            print(f"{key}: {value}")
    else:
        print(result)
    print("-" * 72)


# ---------------------------------------------------------------------------
# Checkpoint helper used by console HITL / external-response flows
# ---------------------------------------------------------------------------


def update_checkpoint_state(
    run_id: str,
    updates: dict[str, Any],
    status: str = "running",
) -> dict[str, Any]:
    from state_graph.checkpointer import load_checkpoint, save_checkpoint

    checkpoint = load_checkpoint(run_id)
    if checkpoint is None:
        raise ValueError(f"No checkpoint found for run_id={run_id}")

    state = {**checkpoint["state"], **updates}
    save_checkpoint(
        run_id=run_id,
        graph_name=checkpoint["graph_name"],
        current_node=checkpoint["current_node"],
        state=state,
        status=status,
    )
    return state


# ---------------------------------------------------------------------------
# 1. Memory & RAG
# ---------------------------------------------------------------------------

async def run_memory_rag() -> None:
    # THIS is the real project import:
    from agent.agent import run_agent

    print("\n[1] Memory & RAG Agent")
    user_id = ask("Customer/User ID", "C001")
    question = ask("Question")

    if not question:
        print("Question cannot be empty.")
        return

    print("\nRouting -> agent.agent.run_agent()")
    try:
        result = await run_agent(
            client=get_local_client(),
            user_input=question,
            user_id=user_id,
        )
        show_result(result)
    except Exception as exc:
        print(f"\nMemory & RAG Agent error: {exc}")
        print("No website/API layer was involved.")


# ---------------------------------------------------------------------------
# 2. Flight Agent
# ---------------------------------------------------------------------------

async def run_flight() -> None:
    # THIS is the real project graph import:
    from state_graph.graphs.flight_rebooking import start_run, resume_run

    print("\n[2] Flight Agent")
    run_id = ask("Run ID", f"flight-console-{int(time.time())}")
    flight_id = ask_int("Flight ID", 2)
    customer_id = ask_int("Customer ID", 5)
    vip = ask_yes_no("Is the customer VIP?", False)

    initial_state = {
        "flight_id": flight_id,
        "customer_id": customer_id,
        "customer_is_vip": vip,
        "customer_response": None,
        "connected_services": None,
        "rebooking_plan": None,
        "alternatives_tried": [],
        "proposed_alternative": None,
        "airline_response": None,
        "refund_amount": None,
        "refund_decision": None,
        "refund_approved": None,
        "final_outcome": None,
    }

    print("\nRouting -> state_graph.graphs.flight_rebooking.start_run()")
    try:
        result = start_run(run_id, initial_state)
        show_result(result)

        if result.get("final_node") == "awaiting_customer_response":
            response = ask(
                "Customer response (rebook/refund/timeout_no_reply)",
                "rebook",
            ).lower()
            if response not in {"rebook", "refund", "timeout_no_reply"}:
                print("Invalid response. Run remains paused.")
                return

            update_checkpoint_state(run_id, {"customer_response": response})
            result = resume_run(run_id)
            show_result(result)

        if result.get("final_node") == "awaiting_airline_response":
            airline_response = ask(
                "Airline response (accepted/rejected)",
                "accepted",
            ).lower()
            update_checkpoint_state(
                run_id,
                {"airline_response": airline_response},
            )
            result = resume_run(run_id)
            show_result(result)

    except Exception as exc:
        print(f"\nFlight Agent error: {exc}")
        print("This graph uses the project's durable MySQL checkpoint layer.")


# ---------------------------------------------------------------------------
# 3. Planning Agent
# ---------------------------------------------------------------------------

async def run_planning() -> None:
    # THIS is the real project import:
    from planning import planning_agent as planning_module
    from planning.environment import TravelEnvironment

    print("\n[3] Planning Agent")
    goal = ask("Planning goal")
    if not goal:
        print("Planning goal cannot be empty.")
        return

    mode = ask("Mode (decomposition_first/dynamic)", "decomposition_first")
    if mode not in {"decomposition_first", "dynamic"}:
        print("Invalid mode; using decomposition_first.")
        mode = "decomposition_first"

    # The ZIP contains a small mismatch:
    # planning_agent.py calls TravelEnvironment(mcp_client=...), while
    # planning/environment.py defines mcp_tools=....
    # We adapt that mismatch here without changing the existing planner.
    class ConsoleTravelEnvironment(TravelEnvironment):
        def __init__(self, mcp_client=None, **kwargs):
            super().__init__(mcp_tools={})
            self.mcp_tools = getattr(mcp_client, "_tools", {}) if mcp_client else {}

    original_environment = planning_module.TravelEnvironment
    planning_module.TravelEnvironment = ConsoleTravelEnvironment

    try:
        print("\nRouting -> planning.planning_agent.run_planning_agent()")
        result = await planning_module.run_planning_agent(
            client=get_local_client(),
            goal=goal,
            mode=mode,
        )
        show_result(result)
    except Exception as exc:
        print(f"\nPlanning Agent error: {exc}")
    finally:
        planning_module.TravelEnvironment = original_environment


# ---------------------------------------------------------------------------
# 4. Refund Agent
# ---------------------------------------------------------------------------

async def run_refund() -> None:
    # THESE are the real project imports:
    from state_graph.refundGraph.refund_graph import start_run, resume_run
    from state_graph.refundGraph.hitl import apply_human_decision

    print("\n[4] Refund Agent")
    run_id = ask("Run ID", f"refund-console-{int(time.time())}")
    booking_id = ask_int("Booking ID", 101)
    employee_id = ask_int("Employee ID", 5)

    print("\nRouting -> state_graph.refundGraph.refund_graph.start_run()")
    try:
        result = await start_run(
            run_id=run_id,
            initial_state={
                "booking_id": booking_id,
                "employee_id": employee_id,
            },
            tools=get_local_client()._tools,
        )
        show_result(result)

        if result.get("final_node") == "hitl_approval":
            approved = ask_yes_no("Approve this refund?", True)
            reason = ask("Decision reason", "Console demo decision")

            apply_human_decision(
                run_id=run_id,
                approved=approved,
                approver_id=employee_id,
                reason=reason,
            )

            result = await resume_run(
                run_id=run_id,
                tools=get_local_client()._tools,
            )
            show_result(result)

        if result.get("final_node") == "waiting_response":
            processor_response = ask(
                "Refund processor response (approved/rejected)",
                "approved",
            ).lower()

            update_checkpoint_state(
                run_id,
                {"refund_response": processor_response},
            )

            result = await resume_run(
                run_id=run_id,
                tools=get_local_client()._tools,
            )
            show_result(result)

    except Exception as exc:
        print(f"\nRefund Agent error: {exc}")
        print("This graph uses the project's durable MySQL checkpoint layer.")


# ---------------------------------------------------------------------------
# 5. VIP Agent
# ---------------------------------------------------------------------------


def run_vip() -> None:
    # THESE are the real project imports:
    from langgraph.types import Command
    from state_graph.graphs.vip_trip_customization import vip_trip_graph

    print("\n[5] VIP Agent")
    customer_id = ask("Customer ID", "C001")
    thread_id = ask("Thread ID", f"vip-console-{uuid.uuid4().hex[:8]}")

    config = {"configurable": {"thread_id": thread_id}}

    print("\nRouting -> state_graph.graphs.vip_trip_customization.vip_trip_graph")
    try:
        result = vip_trip_graph.invoke({"customer_id": customer_id}, config)

        while "__interrupt__" in result:
            interrupts = result["__interrupt__"]
            payload = interrupts[0].value if interrupts else "Manager approval required."

            print("\n" + "=" * 72)
            print("VIP HUMAN APPROVAL")
            print("=" * 72)
            print(payload)

            approved = ask_yes_no("Approve VIP customization?", True)
            result = vip_trip_graph.invoke(
                Command(resume="approved" if approved else "rejected"),
                config,
            )

        show_result(result)
    except Exception as exc:
        print(f"\nVIP Agent error: {exc}")


# ---------------------------------------------------------------------------
# Main menu / router
# ---------------------------------------------------------------------------

MENU = {
    "1": ("Memory & RAG Agent", run_memory_rag),
    "2": ("Flight Agent", run_flight),
    "3": ("Planning Agent", run_planning),
    "4": ("Refund Agent", run_refund),
    "5": ("VIP Agent", run_vip),
}


async def main() -> None:
    banner()

    while True:
        print("\nChoose an agent:")
        for key, (name, _) in MENU.items():
            print(f"  {key}. {name}")
        print("  0. Exit")

        choice = input("\nYour choice: ").strip()

        if choice == "0":
            print("\nWanderPath console closed.")
            return

        item = MENU.get(choice)
        if item is None:
            print("Invalid choice. Select 0-5.")
            continue

        name, handler = item
        print("\n" + "=" * 72)
        print(f"ROUTING -> {name}")
        print("=" * 72)

        try:
            if asyncio.iscoroutinefunction(handler):
                await handler()
            else:
                handler()
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
        except Exception as exc:
            print(f"\nUnexpected error in {name}: {exc}")

        pause()


if __name__ == "__main__":
    asyncio.run(main())
