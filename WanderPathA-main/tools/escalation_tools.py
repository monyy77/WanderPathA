from datetime import datetime
from langchain.tools import tool
from shared.validation import (
    booking_exists,
    customer_exists,
    escalation_exists,
)

from shared.database import get_connection
from shared.authorization import support_or_higher


@tool(
    "escalate_to_human",
    return_direct=False,
    description="Escalate a customer case to a human support agent."
)
def escalate_to_human(
    booking_id: int,
    employee_id: int,
    reason: str,
) -> dict:

    booking_exists(booking_id)
    support_or_higher(employee_id)

    if not reason.strip():
        raise ValueError("Reason cannot be empty.")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Escalations
        (booking_id, employee_id, reason, status, created_date)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        booking_id,
        employee_id,
        reason,
        "Escalated",
        datetime.now(),
    ))

    conn.commit()

    escalation_id = cursor.lastrowid

    cursor.close()
    conn.close()

    return {
        "escalation_id": escalation_id,
        "status": "Escalated",
    }


@tool(
    "create_support_ticket",
    return_direct=False,
    description="Create a support ticket for a customer issue."
)
def create_support_ticket(
    booking_id: int,
    employee_id: int,
    issue: str,
) -> dict:

    booking_exists(booking_id)
    support_or_higher(employee_id)

    if not issue.strip():
        raise ValueError("Issue cannot be empty.")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Escalations
        (booking_id, employee_id, reason, status, created_date)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        booking_id,
        employee_id,
        issue,
        "Open",
        datetime.now(),
    ))

    conn.commit()

    ticket_id = cursor.lastrowid

    cursor.close()
    conn.close()

    return {
        "ticket_id": ticket_id,
        "status": "Open",
    }


@tool(
    "schedule_agent_callback",
    return_direct=False,
    description="Schedule a callback from a support agent."
)
def schedule_agent_callback(
    customer_id: str,
    phone: str,
    callback_time: str,
) -> dict:

    customer_exists(customer_id)

    if not phone.strip():
        raise ValueError("Phone number is required.")

    if not callback_time.strip():
        raise ValueError("Callback time is required.")

    return {
        "customer_id": customer_id,
        "phone": phone,
        "callback_time": callback_time,
        "status": "Callback Scheduled",
    }


@tool(
    "notify_supervisor",
    return_direct=False,
    description="Notify a supervisor about an escalated case."
)
def notify_supervisor(escalation_id: int):

    escalation = escalation_exists(escalation_id)

    return {
        "status": "Supervisor Notified",
        "escalation": escalation,
    }


@tool(
    "log_escalation",
    return_direct=False,
    description="Log the reason for escalating a customer case."
)
def log_escalation(
    escalation_id: int,
    employee_id: int,
    reason: str,
) -> dict:

    support_or_higher(employee_id)
    escalation_exists(escalation_id)

    if not reason.strip():
        raise ValueError("Reason cannot be empty.")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE Escalations
        SET reason = %s
        WHERE escalation_id = %s
    """, (
        reason,
        escalation_id,
    ))

    conn.commit()

    cursor.close()
    conn.close()

    return {
        "escalation_id": escalation_id,
        "status": "Updated",
    }
