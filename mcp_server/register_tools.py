"""
Runtime MCP tool registration.

This module imports the existing WanderPathA tools and
registers them with the FastMCP server.
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


# =========================================================
# AVAILABLE WANDERPATH TOOLS
# =========================================================

TOOLS = [
    # Booking
    get_nearby_airports,
    get_flight_options,
    get_bookings_by_flight,

    # Customer
    get_customer_profile,
    get_booking_history,
    UpdateCustomerProfile,

    # Finance / Decision
    CalculateTripCost,
    CheckRefundEligibility,
    CalculateRefundAmount,
    ProcessRefund,
    CalculateCompensation,
    IssueTravelVoucher,
    CompareRebookingCost,

    # Travel Status
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

    # Escalation
    escalate_to_human,
    create_support_ticket,
    schedule_agent_callback,
    notify_supervisor,
    log_escalation,
]


# =========================================================
# REGISTER TOOLS
# =========================================================

def register_runtime_tools(mcp) -> None:
    """
    Register all existing WanderPathA tools with FastMCP.

    The original LangChain tool function is registered directly
    so FastMCP can preserve the function's input schema.
    """

    for tool in TOOLS:
        mcp.add_tool(
            tool.func,
            name=tool.name,
            description=tool.description,
        )