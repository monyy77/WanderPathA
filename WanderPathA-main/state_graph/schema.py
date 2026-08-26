from typing import TypedDict, Optional


class TripCustomizationState(TypedDict):

    customer_id: str

    vip: bool

    requirements: list

    plan: list

    current_task: Optional[str]

    current_step:int

    completed_task: Optional[str]

    completed_tasks:list


    status: str


    execution_status: str


    service_status: str


    # Failure Recovery

    failed_task: Optional[str]

    failure_reason: Optional[str]

    ticket_id: Optional[str]

    ticket_status: Optional[str]

    current_checkpoint: Optional[str]

    waiting_checks: Optional[int]


    # HITL

    approval_required: Optional[bool]

    approval_status: Optional[str]

    manager_decision: Optional[str]


    # Finalization

    booking_id: Optional[str]

    booking_status: Optional[str]

    database_status: Optional[str]

    final_response: Optional[str]
