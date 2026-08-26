"""
Static resources for the Travel Agency MCP Server.

These resources provide company policies and reference information
that the LLM can read directly instead of invoking a tool.
"""

REFUND_POLICY = """
Refund Policy

• Refunds are available only for bookings marked as refundable.
• Non-refundable tickets cannot be refunded unless the airline cancels the flight.
• Refund requests are processed within 5–7 business days.
• The refunded amount depends on the ticket type and fare conditions.
"""

CANCELLATION_POLICY = """
Cancellation Policy

• Customers may cancel their booking before departure.
• Cancellation fees depend on the ticket type.
• If the airline cancels the flight, customers may choose:
  - Full refund
  - Free rebooking
"""

VIP_BENEFITS = """
VIP Benefits

• Priority customer support.
• Priority rebooking.
• Higher compensation eligibility during disruptions.
• Complimentary travel vouchers when applicable.
• Faster refund processing.
"""

TRAVEL_VOUCHER_RULES = """
Travel Voucher Rules

• Travel vouchers are valid for 12 months.
• Vouchers cannot be exchanged for cash.
• One voucher may be used per booking.
• Lost or expired vouchers cannot be replaced.
"""

AIRPORT_INFORMATION = """
Airport Information

Airport Status:
- Open
- Delayed
- Closed

Weather conditions may affect departures and arrivals.

Passengers may be offered alternative transportation when available.
"""

COMPENSATION_POLICY = """
Compensation Policy

Compensation depends on the delay duration.

• Delay less than 2 hours:
  No compensation.

• Delay from 2 hours to 6 hours:
  Meal voucher.

• Delay more than 6 hours:
  Hotel accommodation and travel voucher.

• Flight cancellation:
  Full refund or free rebooking according to airline policy.
"""
