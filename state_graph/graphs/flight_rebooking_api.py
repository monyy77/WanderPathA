"""
state_graph/graphs/flight_rebooking_api.py

FastAPI adapter for the Flight Rebooking graph.

The API layer does NOT contain graph logic.
It only:
1. Starts a graph run.
2. Reads the current checkpoint.
3. Records external events into the state.
4. Calls resume_run().

Graph logic lives in flight_rebooking.py.
"""

from enum import Enum
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from state_graph.checkpointer import load_checkpoint, save_checkpoint
from state_graph.graphs.flight_rebooking import start_run, resume_run


router = APIRouter(
    prefix="/graphs/flight-rebooking",
    tags=["flight-rebooking-graph"],
)


# ============================================================
# Constants
# ============================================================

GRAPH_NAME = "flight_rebooking"

CUSTOMER_WAIT_NODE = "awaiting_customer_response"
AIRLINE_WAIT_NODE = "awaiting_airline_response"

HITL_REFUND_NODE = "hitl_refund_approval"
HITL_NO_RESPONSE_NODE = "hitl_no_response"


# ============================================================
# Enums
# ============================================================

class CustomerResponse(str, Enum):
    REBOOK = "rebook"
    REFUND = "refund"
    TIMEOUT_NO_REPLY = "timeout_no_reply"


class AirlineResponse(str, Enum):
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


# ============================================================
# Request Models
# ============================================================

class StartRunRequest(BaseModel):
    run_id: str = Field(..., min_length=1)

    flight_id: int
    customer_id: int

    customer_is_vip: bool = False

    connected_services: Optional[list[str]] = None

    refund_amount: Optional[float] = Field(
        default=None,
        ge=0,
    )

    origin_airport: Optional[str] = None
    destination_airport: Optional[str] = None


class CustomerResponseRequest(BaseModel):
    customer_response: CustomerResponse


class AirlineResponseRequest(BaseModel):
    airline_response: AirlineResponse


class HitlResolveRequest(BaseModel):
    # Used when current node == hitl_refund_approval
    refund_approved: Optional[bool] = None

    # Used when current node == hitl_no_response
    customer_response: Optional[CustomerResponse] = None


# ============================================================
# Helpers
# ============================================================

def _get_checkpoint_or_404(run_id: str) -> dict[str, Any]:
    checkpoint = load_checkpoint(run_id)

    if checkpoint is None:
        raise HTTPException(
            status_code=404,
            detail=f"No run found with run_id={run_id}",
        )

    return checkpoint


def _result_response(
    run_id: str,
    result: dict[str, Any],
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "current_node": result["final_node"],
        "status": result["status"],
        "state": result.get("state"),
    }


# ============================================================
# START
# ============================================================

@router.post("/start")
def start_run_endpoint(request: StartRunRequest):
    """
    Starts a brand-new flight rebooking graph run.

    The graph itself decides where execution pauses.
    Usually the first pause is awaiting_customer_response.
    """

    # Prevent accidental restart of an existing run.
    existing = load_checkpoint(request.run_id)

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Run '{request.run_id}' already exists. "
                "Use the existing run instead of starting it again."
            ),
        )

    initial_state = request.model_dump(
        exclude={"run_id"}
    )

    try:
        result = start_run(
            request.run_id,
            initial_state,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start flight rebooking run: {exc}",
        ) from exc

    return _result_response(
        request.run_id,
        result,
    )


# ============================================================
# GET STATUS
# ============================================================

@router.get("/{run_id}")
def get_run_status(run_id: str):
    """
    Returns the latest durable checkpoint for a run.

    Useful for:
    - admin dashboards
    - customer support UI
    - HITL screens
    - debugging
    """

    checkpoint = _get_checkpoint_or_404(run_id)

    return {
        "run_id": run_id,
        "graph_name": checkpoint["graph_name"],
        "current_node": checkpoint["current_node"],
        "status": checkpoint["status"],
        "state": checkpoint["state"],
        "created_at": checkpoint.get("created_at"),
    }


# ============================================================
# CUSTOMER RESPONSE
# ============================================================

@router.post("/{run_id}/customer-response")
def submit_customer_response(
    run_id: str,
    request: CustomerResponseRequest,
):
    """
    Records the customer's external response and resumes the graph.

    Allowed only while the graph is waiting at:
        awaiting_customer_response
    """

    checkpoint = _get_checkpoint_or_404(run_id)

    current_node = checkpoint["current_node"]

    if current_node != CUSTOMER_WAIT_NODE:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Run '{run_id}' is currently at "
                f"'{current_node}', not "
                f"'{CUSTOMER_WAIT_NODE}'."
            ),
        )

    state = {
        **checkpoint["state"],
        "customer_response": request.customer_response.value,
    }

    save_checkpoint(
        run_id=run_id,
        graph_name=GRAPH_NAME,
        current_node=CUSTOMER_WAIT_NODE,
        state=state,
        status="waiting_external",
    )

    try:
        result = resume_run(run_id)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resume run: {exc}",
        ) from exc

    return _result_response(
        run_id,
        result,
    )


# ============================================================
# AIRLINE RESPONSE
# ============================================================

@router.post("/{run_id}/airline-response")
def submit_airline_response(
    run_id: str,
    request: AirlineResponseRequest,
):
    """
    Records the airline's webhook response and resumes the graph.

    Allowed only while the graph is waiting at:
        awaiting_airline_response
    """

    checkpoint = _get_checkpoint_or_404(run_id)

    current_node = checkpoint["current_node"]

    if current_node != AIRLINE_WAIT_NODE:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Run '{run_id}' is currently at "
                f"'{current_node}', not "
                f"'{AIRLINE_WAIT_NODE}'."
            ),
        )

    state = {
        **checkpoint["state"],
        "airline_response": request.airline_response.value,
    }

    save_checkpoint(
        run_id=run_id,
        graph_name=GRAPH_NAME,
        current_node=AIRLINE_WAIT_NODE,
        state=state,
        status="waiting_external",
    )

    try:
        result = resume_run(run_id)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resume run: {exc}",
        ) from exc

    return _result_response(
        run_id,
        result,
    )


# ============================================================
# HITL RESOLUTION
# ============================================================

@router.post("/{run_id}/hitl-resolve")
def resolve_hitl(
    run_id: str,
    request: HitlResolveRequest,
):
    """
    Resolves a pending HITL decision and resumes the graph.

    Supported HITL nodes:

    1. hitl_refund_approval
       -> admin provides refund_approved

    2. hitl_no_response
       -> admin provides customer_response
    """

    checkpoint = _get_checkpoint_or_404(run_id)

    current_node = checkpoint["current_node"]

    if current_node not in (
        HITL_REFUND_NODE,
        HITL_NO_RESPONSE_NODE,
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                f"Run '{run_id}' is currently at "
                f"'{current_node}', not a pending HITL node."
            ),
        )

    state = dict(checkpoint["state"])

    # --------------------------------------------------------
    # HITL: Refund approval
    # --------------------------------------------------------

    if current_node == HITL_REFUND_NODE:

        if request.refund_approved is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "refund_approved is required when "
                    "resolving hitl_refund_approval."
                ),
            )

        state["refund_approved"] = request.refund_approved

    # --------------------------------------------------------
    # HITL: Customer did not respond
    # --------------------------------------------------------

    else:

        if request.customer_response is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "customer_response is required when "
                    "resolving hitl_no_response."
                ),
            )

        state["customer_response"] = (
            request.customer_response.value
        )

    # Important:
    # This is an admin action, so the checkpoint is explicitly
    # marked as paused_hitl before resume_run() continues it.
    save_checkpoint(
        run_id=run_id,
        graph_name=GRAPH_NAME,
        current_node=current_node,
        state=state,
        status="paused_hitl",
    )

    try:
        result = resume_run(run_id)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resume HITL run: {exc}",
        ) from exc

    return _result_response(
        run_id,
        result,
    )