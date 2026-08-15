import sys
import os
from fastmcp import FastMCP , Context
from mcp.types import ElicitRequestedSchema
from typing import Literal
import asyncio

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(parent_dir)

import mcp.types as types 
from shared.database import get_connection



current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(parent_dir)
from tools.travel_status_tools import (
    get_flight_status,
    get_weather,
    get_delay_duration,
    check_disruption_reason,
    check_connection_risk,
    get_disruption_severity,
    check_alternative_transport,
)
from tools.booking_tools import (
    get_nearby_airports,
    get_flight_options,
    get_bookings_by_flight,
)
from tools.customer_tools import (
    get_customer_profile,
    get_booking_history
)
from tools.finance_and_decision_tools import (
    ProcessRefund,
    CalculateRefundAmount,
    CalculateCompensation,
)
from tools.escalation_tools import escalate_to_human
from shared.prompts import *
from shared.resources import *


# Initialize FastMCP server for WanderPathA
mcp = FastMCP("WanderPathA Travel Agent Server")



# --- VIP-only tools, unlocked at runtime -----------------------------------
# These tools do not exist for non-VIP customers. They are registered on the
# server the moment a customer is genuinely upgraded (a real DB state change),
# not on a timer, not on every request, and not via a "simulate" tool.
_vip_tools_registered = False


def _register_vip_tools():
    """Register VIP-only tools exactly once, the first time any customer
    is upgraded. Idempotent so repeat upgrades never re-register or send
    duplicate notifications."""
    global _vip_tools_registered
    if _vip_tools_registered:
        return
    _vip_tools_registered = True

    @mcp.tool()
    async def request_priority_rebooking(
        ctx: Context, booking_id: int, preferred_flight_id: int
    ):
        """VIP-only: Rebook a disrupted booking onto a preferred flight with
        no change fee and priority queueing."""
        return {
            "status": "success",
            "message": (
                f"Booking {booking_id} priority-rebooked onto flight "
                f"{preferred_flight_id}. Change fee waived (VIP)."
            ),
        }

    @mcp.tool()
    async def request_concierge_service(ctx: Context, customer_id: int, request: str):
        """VIP-only: Submit a concierge request (lounge access, ground
        transport, special assistance) for a VIP customer."""
        return {
            "status": "success",
            "message": f"Concierge request logged for customer {customer_id}: {request}",
        }


@mcp.tool()
async def upgrade_to_vip(ctx: Context, customer_id: int):
    """
    Upgrade a customer to VIP status. The first time this happens on this
    server, VIP-only tools (priority rebooking, concierge requests) become
    available and a tools/list_changed notification is sent.
    """

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Check customer exists
        cursor.execute(
            "SELECT vip FROM Customers WHERE customer_id = %s",
            (customer_id,)
        )

        customer = cursor.fetchone()

        if customer is None:
            return {
                "status": "error",
                "message": f"Customer {customer_id} not found."
            }

        if customer[0]:
            # Already VIP: no state change, so no notification is sent.
            return {
                "status": "success",
                "message": f"Customer {customer_id} is already a VIP."
            }

        cursor.execute(
            """
            UPDATE Customers
            SET vip = TRUE
            WHERE customer_id = %s
            """,
            (customer_id,)
        )

        conn.commit()

        # --- Genuine runtime state change -> unlock tools, then notify ---
        was_already_registered = _vip_tools_registered
        _register_vip_tools()

        if not was_already_registered:
            # Logging channel: lets the demo client show *what* changed.
            await ctx.info(f"__EVENT__:VIP_UNLOCKED:{customer_id}")
            # Official MCP notification per spec.
            await ctx.session.send_tool_list_changed()
            print(f"[NOTIFICATION] tools/list_changed sent (customer {customer_id} -> VIP)")

        return {
            "status": "success",
            "message": (
                f"Customer {customer_id} has been upgraded to VIP. "
                f"VIP tools are now available."
            )
        }

    except Exception as e:
        conn.rollback()
        return {
            "status": "error",
            "message": str(e)
        }

    finally:
        cursor.close()
        conn.close()

# Register Existing Tools
mcp.tool()(get_flight_status.func)
mcp.tool()(get_weather.func)
mcp.tool()(get_delay_duration.func)
mcp.tool()(check_disruption_reason.func)
mcp.tool()(get_nearby_airports.func)
mcp.tool()(get_flight_options.func)
mcp.tool()(get_customer_profile.func)
mcp.tool()(get_booking_history.func)

# --- Registered for the Planning Agent (IROPS reshuffle) -------------------
# These tools already existed in tools/*.py but were not yet wired onto the
# server. Registering them, not rebuilding them, per the lab's "reuse the
# existing server and tools" requirement. get_bookings_by_flight is the one
# genuinely new tool: nothing previously covered "which bookings/customers
# are on this disrupted flight".
mcp.tool()(get_bookings_by_flight.func)
mcp.tool()(check_connection_risk.func)
mcp.tool()(get_disruption_severity.func)
mcp.tool()(check_alternative_transport.func)
mcp.tool()(CalculateCompensation.func)
mcp.tool()(escalate_to_human.func)
mcp.prompt()(refund_explanation)
mcp.prompt()(explain_flight_delay)
mcp.prompt()(travel_voucher_message)
mcp.prompt()(rebooking_options)
mcp.prompt()(booking_confirmation)
mcp.prompt()(flight_cancellation_notice)
@mcp.resource("docs://refund-policy")
def refund_policy():
    return REFUND_POLICY


@mcp.resource("docs://cancellation-policy")
def cancellation_policy():
    return CANCELLATION_POLICY


@mcp.resource("docs://vip-benefits")
def vip_benefits():
    return VIP_BENEFITS


@mcp.resource("docs://travel-voucher-rules")
def travel_voucher_rules():
    return TRAVEL_VOUCHER_RULES


@mcp.resource("docs://airport-information")
def airport_information():
    return AIRPORT_INFORMATION


@mcp.resource("docs://compensation-policy")
def compensation_policy():
    return COMPENSATION_POLICY

# Elication
@mcp.tool()
async def refund_with_confirmation(
    ctx: Context,
    booking_id: int,
):
    """Process a refund after explicit user confirmation."""

    print("=== refund_with_confirmation started ===")

    employee_id = 3

    print("1. Reporting progress...")
    await ctx.report_progress(
        progress=10,
        total=100,
        message="Calculating refund amount..."
    )

    print("2. Calculating refund amount...")
    refund_amount = CalculateRefundAmount.func(
        booking_id=booking_id
    )
    print(f"Refund amount = {refund_amount}")

    await asyncio.sleep(1)

    print("3. Reporting progress...")
    await ctx.report_progress(
        progress=40,
        total=100,
        message="Waiting for customer confirmation..."
    )

    print("4. Waiting for elicitation...")
    result = await ctx.elicit(
        message=(
            f"You are about to refund ${refund_amount:.2f} "
            f"for booking {booking_id}.\n\n"
        ),
        response_type=Literal["confirm", "cancel"],
    )

    print("Elicitation result:", result)

    if result.action != "accept":
        print("User declined.")
        return {
            "status": "Cancelled",
            "message": "Refund cancelled by user."
        }

    if result.data != "confirm":
        print("User did not type confirm.")
        return {
            "status": "Cancelled",
            "message": "Refund cancelled by user."
        }

    print("5. Reporting progress...")
    await ctx.report_progress(
        progress=70,
        total=100,
        message="Processing refund..."
    )

    await asyncio.sleep(1)

    print("6. Calling ProcessRefund...")
    refund_result = ProcessRefund.func(
        booking_id=booking_id,
        employee_id=employee_id,
        refund_amount=refund_amount,
    )

    print("ProcessRefund returned:", refund_result)

    print("7. Reporting completion...")
    await ctx.report_progress(
        progress=100,
        total=100,
        message="Refund completed."
    )

    print("=== refund_with_confirmation finished ===")

    return refund_result

# Sampling 
@mcp.tool()
async def evaluate_cancellation_reason(
    ctx: Context,
    booking_id: int,
    user_reason: str = "",
    cancellation_reason: str = "",
    reason: str = "",
    user_id: str = "",
) -> str:
  """Evaluates refund eligibility using LLM sampling with automated fallback."""
  eval_reason = reason or user_reason or cancellation_reason or "Emergency"
  b_id = booking_id or "BK-9921"

  prompt = (
      f"Evaluate the travel cancellation reason: '{eval_reason}'. Does it"
      " qualify for a 100% full refund according to emergency travel policy?"
      " Respond ONLY with 'APPROVED' or 'DENIED' followed by a brief"
      " explanation."
  )

  try:
    sampling_response = await ctx.session.create_message(
        messages=[{"role": "user", "content": prompt}], max_tokens=100
    )

    llm_output = ""
    if hasattr(sampling_response, "content") and sampling_response.content:
      if isinstance(sampling_response.content, list):
        llm_output = "\n".join(
            [getattr(c, "text", str(c)) for c in sampling_response.content]
        )
      else:
        llm_output = getattr(
            sampling_response.content, "text", str(sampling_response.content)
        )

    return (
        f"Policy Evaluation Result for Booking {b_id} (via LLM"
        f" Sampling):\n{llm_output.strip()}"
    )

  except Exception as e:
    # Fallback 
    print(f"[Sampling Attempt Logged]: {e}")

    reason_lower = eval_reason.lower()
    if any(
        kw in reason_lower
        for kw in [
            "flood",
            "weather",
            "medical",
            "emergency",
            "hospital",
            "submerged",
        ]
    ):
      return (
          f"Policy Evaluation Result for Booking {b_id}: APPROVED\nAnalysis:"
          " Severe emergency condition qualifies for 100% full refund under"
          " policy."
      )

    return (
        f"Policy Evaluation Result for Booking {b_id}: DENIED\nAnalysis:"
        " Reason does not qualify for full refund. Standard 20% cancellation"
        " fee applies."
    )
  
if __name__ == "__main__":
    transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    if transport == "stdio":
        sys.stderr.write("Starting WanderPathA Server [stdio]...")
        mcp.run(transport="stdio")
    elif transport == "http":
        sys.stderr.write("Starting WanderPathA Server [http:8080]...")
        mcp.run(transport="streamable-http", host="0.0.0.0", port=8080)
