from dataclasses import dataclass

from langchain.tools import tool

from shared.database import get_connection
from shared.validation import customer_exists



@dataclass
class AgentContext:
    user_id: str



@tool(
    "get_customer_profile",
    return_direct=False,
    description="Get the customer profile based on the provided customer ID.",
)
def get_customer_profile(user_id: str) -> dict:


    customer_exists(user_id)


    conn = get_connection()
    cursor = conn.cursor(dictionary=True)


    cursor.execute(
        """
        SELECT *
        FROM Customers
        WHERE customer_id = %s
        """,
        (user_id,)
    )


    customer = cursor.fetchone()


    cursor.close()
    conn.close()


    return customer




@tool(
    "get_booking_history",
    return_direct=False,
    description="Get the booking history for the current customer."
)
def get_booking_history(user_id: str) -> list:


    customer_exists(user_id)


    conn = get_connection()
    cursor = conn.cursor(dictionary=True)


    cursor.execute(
        """
        SELECT *
        FROM Bookings
        WHERE customer_id = %s
        """,
        (user_id,)
    )


    bookings = cursor.fetchall()


    cursor.close()
    conn.close()


    return bookings




@tool(
    "update_customer_profile",
    return_direct=False,
    description="Update the customer profile."
)
def UpdateCustomerProfile(
    user_id: str,
    first_name: str,
    last_name: str,
    email: str,
    phone: str,
) -> dict:


    customer_exists(user_id)


    if not first_name.strip():
        raise ValueError(
            "First name is required."
        )


    if not last_name.strip():
        raise ValueError(
            "Last name is required."
        )


    if not email.strip():
        raise ValueError(
            "Email is required."
        )


    if not phone.strip():
        raise ValueError(
            "Phone number is required."
        )


    conn = get_connection()
    cursor = conn.cursor()


    cursor.execute(
        """
        UPDATE Customers
        SET
            first_name=%s,
            last_name=%s,
            email=%s,
            phone=%s
        WHERE customer_id=%s
        """,
        (
            first_name,
            last_name,
            email,
            phone,
            user_id,
        )
    )


    conn.commit()


    cursor.close()
    conn.close()


    return {
        "customer_id": user_id,
        "status": "Profile Updated",
    }