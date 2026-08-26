from langchain.tools import tool
from shared.validation import (
    booking_exists,
    validate_refund_amount,
    validate_voucher_value,
)
from shared.database import get_connection
from shared.authorization import manager_required
from datetime import datetime

@tool(
    "calculate_trip_cost",
    return_direct=False,
    description="Calculate the total trip cost for a booking."
)
def CalculateTripCost(booking_id: int) -> float:

    booking_exists(booking_id)

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT trip_cost
        FROM Bookings
        WHERE booking_id = %s
    """, (booking_id,))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result["trip_cost"]


@tool(
    "check_refund_eligibility",
    return_direct=False,
    description="Check whether a booking is eligible for a refund."
)
def CheckRefundEligibility(booking_id: int) -> bool:

    booking_exists(booking_id)
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT refund_eligible
        FROM Bookings
        WHERE booking_id = %s
    """, (booking_id,))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result["refund_eligible"]


@tool(
    "calculate_refund_amount",
    return_direct=False,
    description="Calculate the refund amount for a booking."
)
def CalculateRefundAmount(booking_id: int) -> float:

    booking_exists(booking_id)
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT trip_cost
        FROM Bookings
        WHERE booking_id = %s
    """, (booking_id,))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result["trip_cost"] if result else 0


@tool(
    "process_refund",
    return_direct=False,
    description="Process the refund for a booking."
)
def ProcessRefund(
    booking_id: int,
    employee_id: int,
    refund_amount: float,
) -> dict:

    booking_exists(booking_id)
    manager_required(employee_id)
    validate_refund_amount(refund_amount)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Refunds
        (
            booking_id,
            processed_by,
            refund_amount,
            status,
            processed_date
        )
        VALUES (%s,%s,%s,%s,%s)
    """, (
        booking_id,
        employee_id,
        refund_amount,
        "Processed",
        datetime.now(),
    ))

    conn.commit()

    refund_id = cursor.lastrowid

    cursor.close()
    conn.close()

    return {
        "refund_id": refund_id,
        "status": "Processed",
    }


@tool(
    "calculate_compensation",
    return_direct=False,
    description="Calculate the compensation amount for a booking."
)
def CalculateCompensation(booking_id: int) -> float:

    booking_exists(booking_id)

    eligible = CheckRefundEligibility.invoke(
        {"booking_id": booking_id}
    )

    if eligible:
        return 100.0

    return 0.0


@tool(
    "issue_travel_voucher",
    return_direct=False,
    description="Issue a travel voucher for a booking."
)
def IssueTravelVoucher(
    booking_id: int,
    voucher_value: float,
) -> dict:

    booking_exists(booking_id)
    validate_voucher_value(voucher_value)

    return {
        "booking_id": booking_id,
        "voucher": f"${voucher_value} Travel Voucher",
    }


@tool(
    "compare_rebooking_cost",
    return_direct=False,
    description="Compare the original trip cost with a new rebooking cost."
)
def CompareRebookingCost(
    old_booking_id: int,
    new_booking_cost: float,
) -> str:

    booking_exists(old_booking_id)

    if new_booking_cost <= 0:
        raise ValueError(
            "New booking cost must be greater than zero."
        )

    old_cost = CalculateTripCost.invoke(
        {"booking_id": old_booking_id}
    )
    if new_booking_cost > old_cost:
        return "Additional Payment Required"

    elif new_booking_cost < old_cost:
        return "Refund Difference"

    return "No Price Difference"
