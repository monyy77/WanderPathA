from mcp_server.server import mcp

from tools.flight_tools import (
    get_nearby_airports,
    get_flight_options,
    get_bookings_by_flight,
)

from tools.customer_tools import (
    get_customer_profile,
    get_booking_history,
    UpdateCustomerProfile,
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

from tools.status_tools import (
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



TOOLS = [

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
]


def register_runtime_tools():

    for t in TOOLS:

        @mcp.tool(
            name=t.name,
            description=t.description
        )
        def wrapper(**kwargs):

            return t.invoke(kwargs)