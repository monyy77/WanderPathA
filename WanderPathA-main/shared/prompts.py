"""
Prompt Templates for the Travel Agency MCP Server.

This file contains reusable prompt templates that help the LLM
generate consistent customer support responses for common travel scenarios
such as refunds, flight delays, cancellations, booking confirmations,
travel vouchers, and rebooking options.
"""

#prompt 1
def refund_explanation(
    booking_id: str,
    customer_name: str,
    reason: str,
) -> str:
    return f"""
You are a customer support specialist.

Explain the refund decision to the customer.

Booking ID: {booking_id}
Customer Name: {customer_name}
Reason: {reason}

Write a polite and professional explanation.
"""

#prompt 2
def explain_flight_delay(
    customer_name: str,
    flight_id: str,
    delay_minutes: int,
    reason: str,
) -> str:
    return f"""
You are a travel support agent.

Explain the flight delay.

Customer:
{customer_name}

Flight:
{flight_id}

Delay:
{delay_minutes} minutes

Reason:
{reason}

Be empathetic and concise.
"""

#prompt 3
def travel_voucher_message(
    customer_name: str,
    voucher_value: str,
) -> str:
    return f"""
Write a message informing the customer that a travel voucher has been issued.

Customer:
{customer_name}

Voucher:
{voucher_value}

Explain how it can be used.
"""

#prompt 4
def rebooking_options(
    customer_name: str,
    original_flight: str,
    alternatives: list,
) -> str:
    return f"""
Present alternative flight options.

Customer:
{customer_name}

Original Flight:
{original_flight}

Alternatives:
{alternatives}

Recommend the best option.
"""

#prompt 5
def booking_confirmation(
    customer_name: str,
    booking_id: str,
    flight_id: str,
    departure_date: str,
) -> str:
    return f"""
You are a travel agency assistant.

Write a booking confirmation message.

Customer:
{customer_name}

Booking ID:
{booking_id}

Flight:
{flight_id}

Departure Date:
{departure_date}

Confirm that the booking has been completed successfully.
Include a friendly closing message.
"""

#prompt 6
def flight_cancellation_notice(
    customer_name: str,
    flight_id: str,
    reason: str,
    alternatives: list,
) -> str:
    return f"""
You are a customer support specialist.

Write a professional flight cancellation notice.

Customer:
{customer_name}

Flight:
{flight_id}

Cancellation Reason:
{reason}

Available Alternatives:
{alternatives}

Apologize for the inconvenience.
Clearly explain that the flight has been cancelled.
Present the available alternative flights or travel options.
Use a polite and reassuring tone.
"""
