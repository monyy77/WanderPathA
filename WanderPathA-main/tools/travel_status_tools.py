from langchain.tools import tool
from shared.database import get_connection
from shared.validation import (
    flight_exists,
    airport_exists,
)

@tool(
    "get_flight_status",
    return_direct=False,
    description="Get the current status of a flight."
)
def get_flight_status(flight_id: int) -> str:

    flight_exists(flight_id)

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT status FROM Flights WHERE flight_id=%s",
        (flight_id,)
    )

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result["status"]


@tool(
    "get_delay_duration",
    return_direct=False,
    description="Get the delay duration of a flight in minutes."
)
def get_delay_duration(flight_id: int) -> int:

    flight_exists(flight_id)

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT delay_minutes FROM Flights WHERE flight_id=%s",
        (flight_id,)
    )

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result["delay_minutes"]


@tool(
    "check_disruption_reason",
    return_direct=False,
    description="Get the reason for a flight disruption or delay."
)
def check_disruption_reason(flight_id: int) -> str:

    flight_exists(flight_id)

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT disruption_reason FROM Flights WHERE flight_id=%s",
        (flight_id,)
    )

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result["disruption_reason"]


@tool(
    "get_weather",
    return_direct=False,
    description="Get the current weather conditions at an airport."
)
def get_weather(airport_code: str) -> str:

    airport_exists(airport_code)

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT weather FROM Airports WHERE airport_code=%s",
        (airport_code,)
    )

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result["weather"]


@tool(
    "check_airport_status",
    return_direct=False,
    description="Get the operational status of an airport."
)
def check_airport_status(airport_code: str) -> str:

    airport_exists(airport_code)

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT status FROM Airports WHERE airport_code=%s",
        (airport_code,)
    )

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result["status"]


@tool(
    "check_connection_risk",
    return_direct=False,
    description="Check whether a delayed flight may cause a missed connection."
)
def check_connection_risk(flight_id: int) -> bool:

    flight_exists(flight_id)

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT connection_risk FROM Flights WHERE flight_id=%s",
        (flight_id,)
    )

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result["connection_risk"]


@tool(
    "get_estimated_departure",
    return_direct=False,
    description="Get the estimated departure time of a flight."
)
def get_estimated_departure(flight_id: int):

    flight_exists(flight_id)

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT estimated_departure_time FROM Flights WHERE flight_id=%s",
        (flight_id,)
    )

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result["estimated_departure_time"]


@tool(
    "get_estimated_arrival",
    return_direct=False,
    description="Get the estimated arrival time of a flight."
)
def get_estimated_arrival(flight_id: int):

    flight_exists(flight_id)

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT estimated_arrival_time FROM Flights WHERE flight_id=%s",
        (flight_id,)
    )

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result["estimated_arrival_time"]


@tool(
    "check_alternative_transport",
    return_direct=False,
    description="Get available alternative transportation options for a destination."
)
def check_alternative_transport(destination: str):

    airport_exists(destination)

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM AlternativeTransport
        WHERE destination_airport = %s
    """, (destination,))

    transport = cursor.fetchall()

    cursor.close()
    conn.close()

    return transport


@tool(
    "get_disruption_severity",
    return_direct=False,
    description="Get the severity level of a flight disruption."
)
def get_disruption_severity(flight_id: int):

    flight_exists(flight_id)

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT severity
        FROM Flights
        WHERE flight_id = %s
    """, (flight_id,))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result["severity"]
