from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, create_model


MAX_STEPS = 6
VALIDATION_RETRIES = 2

TERMINAL_ACTIONS = {"escalate", "end_conversation", "final_answer"}


class AgentStep(BaseModel):
    """Fallback/typing reference. The model actually bound for structured
    output is built fresh each turn by build_agent_step_model, since the
    set of valid `action` values changes at runtime (e.g. VIP unlock)."""

    thought: str
    action: str
    action_input: dict = Field(default_factory=dict)
    is_final: bool


def build_agent_step_model(action_names):
    """Builds an AgentStep schema whose `action` field is a Literal
    constrained to exactly the tools available *right now* (plus the
    fixed terminal actions). Called once per agent turn, so a genuine
    runtime tool-list change immediately changes what the LLM is allowed
    to output — no static enum, no restart, no reconnect."""
    allowed = tuple(sorted(set(action_names) | TERMINAL_ACTIONS))
    return create_model(
        "AgentStep",
        thought=(str, ...),
        action=(Literal[allowed], ...),
        action_input=(dict, Field(default_factory=dict)),
        is_final=(bool, ...),
    )


class StrictInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EmptyInput(StrictInput):
    pass


class FlightInput(StrictInput):
    flight_id: str


class DestinationInput(StrictInput):
    destination: str


class BookingInput(StrictInput):
    booking_id: str


class EscalationInput(StrictInput):
    case_id: str


class AnswerInput(StrictInput):
    answer: str


ACTION_INPUT_SCHEMAS = {
    "get_booking_history": EmptyInput,
    "get_flight_status": FlightInput,
    "get_delay_duration": FlightInput,
    "check_alternative_transport": DestinationInput,
    "check_refund_eligibility": BookingInput,
    "calculate_refund_amount": BookingInput,
    "refund_with_confirmation": BookingInput,
    "issue_travel_voucher": BookingInput,
    "escalate": EscalationInput,
    "end_conversation": AnswerInput,
    "final_answer": AnswerInput,
}