from shared.database import get_connection

def booking_exists(booking_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM Bookings WHERE booking_id=%s",
        (booking_id,)
    )

    booking = cursor.fetchone()

    cursor.close()
    conn.close()

    if booking is None:
        raise ValueError(f"Booking {booking_id} does not exist.")

    return booking

def airport_exists(airport_code: str):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM Airports WHERE airport_code = %s",
        (airport_code,)
    )

    airport = cursor.fetchone()

    cursor.close()
    conn.close()

    if airport is None:
        raise ValueError(f"Airport '{airport_code}' does not exist.")

    return airport

def customer_exists(customer_id: str):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM Customers WHERE customer_id=%s",
        (customer_id,)
    )

    customer = cursor.fetchone()

    cursor.close()
    conn.close()

    if customer is None:
        raise ValueError(f"Customer {customer_id} does not exist.")

    return customer


def flight_exists(flight_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM Flights WHERE flight_id=%s",
        (flight_id,)
    )

    flight = cursor.fetchone()

    cursor.close()
    conn.close()

    if flight is None:
        raise ValueError(f"Flight {flight_id} does not exist.")

    return flight


def employee_exists(employee_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM Employees WHERE employee_id=%s",
        (employee_id,)
    )

    employee = cursor.fetchone()

    cursor.close()
    conn.close()

    if employee is None:
        raise ValueError(f"Employee {employee_id} does not exist.")

    return employee

def escalation_exists(escalation_id: int):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM Escalations
        WHERE escalation_id = %s
    """, (escalation_id,))

    escalation = cursor.fetchone()

    cursor.close()
    conn.close()

    if escalation is None:
        raise ValueError(
            f"Escalation {escalation_id} does not exist."
        )

    return escalation


def validate_refund_amount(amount: float):
    if amount <= 0:
        raise ValueError("Refund amount must be greater than zero.")


def validate_voucher_value(value: float):
    if value <= 0:
        raise ValueError("Voucher value must be greater than zero.")


def validate_employee_role(role: str):

    allowed_roles = {
        "Support Agent",
        "Supervisor",
        "Manager",
        "Admin",
    }

    if role not in allowed_roles:
        raise ValueError("Invalid employee role.")
