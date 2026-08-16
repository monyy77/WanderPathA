from langchain.tools import tool
from shared.database import get_connection
from shared.validation import airport_exists

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
