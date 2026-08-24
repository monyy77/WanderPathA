"""
mcp_server/register_tools.py

Registers every LangChain tool inside FastMCP.

Flow:

User Platform
      ↓
FastMCP Client
      ↓
FastMCP Server
      ↓
LangChain Tools
"""

from typing import Callable


# ==========================================================
# Import LangChain Tools
# ==========================================================


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


from tools.customer_tools import (
    get_customer_profile,
    get_booking_history,
    UpdateCustomerProfile,
)


from tools.flight_tools import (
    get_nearby_airports,
    get_flight_options,
    get_bookings_by_flight,
)


from tools.finance_tools import (
    CalculateTripCost,
    CheckRefundEligibility,
    CalculateRefundAmount,
    ProcessRefund,
    CalculateCompensation,
    IssueTravelVoucher,
    CompareRebookingCost,
)


from tools.utility_tools import (
    SearchWeb,
    GetCurrentDate,
    EndConversation,
)



# ==========================================================
# Register One Tool
# ==========================================================


def _register(mcp, langchain_tool):
    """
    Register one LangChain tool inside FastMCP.
    """

    fn: Callable = langchain_tool.func

    name = langchain_tool.name

    description = getattr(
        langchain_tool,
        "description",
        "",
    )


    mcp.tool(
        name=name,
        description=description,
    )(fn)



# ==========================================================
# Register All Tools
# ==========================================================


def register_runtime_tools(mcp):

    """
    Expose all LangChain tools through MCP.
    """


    tools = [

        # ======================
        # Flight Tools
        # ======================

        get_nearby_airports,
        get_flight_options,
        get_bookings_by_flight,


        # ======================
        # Customer Tools
        # ======================

        get_customer_profile,
        get_booking_history,
        UpdateCustomerProfile,


        # ======================
        # Finance Tools
        # ======================

        CalculateTripCost,
        CheckRefundEligibility,
        CalculateRefundAmount,
        ProcessRefund,
        CalculateCompensation,
        IssueTravelVoucher,
        CompareRebookingCost,


        # ======================
        # Travel Status Tools
        # ======================

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


        # ======================
        # Utility Tools
        # ======================

        SearchWeb,
        GetCurrentDate,
        EndConversation,
    ]


    for tool in tools:

        _register(
            mcp,
            tool
        )


    print(
        f"Registered {len(tools)} MCP tools."
    )