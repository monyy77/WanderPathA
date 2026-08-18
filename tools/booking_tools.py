from langchain.tools import tool
from shared.database import get_connection
from shared.validation import airport_exists, flight_exists

@tool(
    "get_nearby_airports",
    return_direct=False,
    description="Get nearby airports based on the provided city.",
)
def get_nearby_airports(city: str) -> list:

    if not city.strip():
        raise ValueError("City is required.")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            airport_code AS skyId,
            airport_name,
            city,
            country,
            weather,
            status
        FROM Airports
        WHERE LOWER(city) = LOWER(%s)
    """, (city,))

    airports = cursor.fetchall()

    cursor.close()
    conn.close()

    return airports


@tool(
    "get_flight_options",
    return_direct=False,
    description="Get flight options based on the provided parameters.",
)
def get_flight_options(
    originSkyId: str,
    destinationSkyId: str,
    departureDate: str,
) -> list:

    if not originSkyId:
        raise ValueError("Origin airport is required.")

    if not destinationSkyId:
        raise ValueError("Destination airport is required.")

    if not departureDate:
        raise ValueError("Departure date is required.")

    airport_exists(originSkyId)
    airport_exists(destinationSkyId)

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM Flights
        WHERE origin_airport = %s
          AND destination_airport = %s
          AND DATE(departure_time) = %s
    """, (
        originSkyId,
        destinationSkyId,
        departureDate,
    ))

    flights = cursor.fetchall()

    cursor.close()
    conn.close()

    return flights


@tool(
    "get_bookings_by_flight",
    return_direct=False,
    description=(
        "Get every booking, with its customer, on a given flight. "
        "Used by the Planning Agent to find all bookings affected by a "
        "flight disruption (delay, cancellation)."
    ),
)
def get_bookings_by_flight(flight_id: int) -> list:

    flight_exists(flight_id)

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            b.booking_id,
            b.customer_id,
            b.status AS booking_status,
            b.ticket_type,
            b.trip_cost,
            b.refund_eligible,
            c.first_name,
            c.last_name,
            c.email,
            c.phone,
            c.vip
        FROM Bookings b
        JOIN Customers c ON c.customer_id = b.customer_id
        WHERE b.flight_id = %s
    """, (flight_id,))

    bookings = cursor.fetchall()

    cursor.close()
    conn.close()

    return bookings
