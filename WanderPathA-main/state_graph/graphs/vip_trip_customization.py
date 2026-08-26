"""
VIP Trip Customization State Graph

Workflow:

START
  |
receive_request
  |
validate_customer
  |
check_vip
  |----------------|
 vip              reject
  |                |
analyze_request   END
  |
planning
  |
Discount Decision Router (evaluate_discount_policy — a router
function, not a graph node; it only decides which edge to take)
  |----------------|
execute         human_approval
  |                |
  |             interrupt()
  |                |
  |          (graph pauses; resumes
  |           via Command(resume=...))
  |                |
  |          check_manager_decision
  |          |----------------|
  |        approved         rejected
  |          |                |
  |          v                v
  |       execute            END
  |
  ├── complete ─────► update_booking ─► update_database ─► generate_final_response ─► END
  |
  ├── failure ──────► failure_handler
  |                       |
  |                       v
  |                    waiting
  |
  └── waiting ───────► waiting
                           |
                     wait_service
                      |        |
                   wait     continue
                      |        |
                      v        v
                  waiting   execute


Checkpoint:
- Save state after each major workflow state
- Allow resume from interrupted execution (both service-wait
  retries and human-in-the-loop manager approval)
"""


from uuid import uuid4

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt

from state_graph.schema import TripCustomizationState



# =========================
# Nodes
# =========================


def receive_request(state: TripCustomizationState):

    print("Receiving customer request")

    return {
        "status": "running"
    }



def validate_customer(state: TripCustomizationState):

    print("Validating customer")

    customer_id = state.get(
        "customer_id"
    )

    # Later:
    # SELECT vip
    # FROM customers
    # WHERE customer_id = %s

    vip = True

    return {
        "vip": vip
    }



# =========================
# VIP Decision
# =========================


def check_vip(state: TripCustomizationState):

    if state.get("vip"):
        return "vip"

    return "reject"



# =========================
# Analysis
# =========================


def analyze_request(state: TripCustomizationState):

    print(
        "Analyzing customization request"
    )

    return {
        "requirements": [
            "upgrade_flight",
            "reserve_hotel",
            "reserve_car",
            "book_tour"
        ]
    }



# =========================
# Planning
# =========================


def run_planning(state: TripCustomizationState):

    print(
        "Running LATS planner"
    )

    plan = [

        {
            "task": "upgrade_flight"
        },

        {
            "task": "reserve_hotel"
        },

        {
            "task": "reserve_car"
        },

        {
            "task": "book_tour"
        }
    ]


    # Architecture note: execute_plan walks this plan one task at
    # a time using "current_step" as an index into it, instead of
    # being pointed at a single hardcoded task. current_task is
    # derived fresh each time execute_plan runs.
    return {

        "plan": plan,

        "current_step": 0

    }


# =========================
# HITL Decision Check
# =========================


def evaluate_discount_policy(
    state: TripCustomizationState
):

    print(
        "Checking discount approval"
    )


    discount = 50


    if discount > 40:

        return "approval"


    return "execute"


# =========================
# Human Approval Node
# =========================


def human_approval(
    state: TripCustomizationState
):

    print(
        "Waiting for manager approval"
    )


    # interrupt() pauses graph execution here and persists the
    # payload below via the checkpointer. Nothing after this
    # line runs until the graph is resumed with
    # Command(resume=<decision>) using the same thread_id.
    decision = interrupt(
        {
            "message":
                "Manager approval required",

            "discount":
                50,

            "checkpoint":
                "human_approval"
        }
    )


    return {

        "approval_required": True,

        "approval_status": "COMPLETED",

        "manager_decision":
            decision,

        "current_checkpoint":
            "human_approval"

    }


def check_manager_decision(
    state: TripCustomizationState
):

    # No "waiting" branch: interrupt() is what pauses the graph.
    # By the time this router runs again, resume(...) has
    # already supplied a decision, so anything other than
    # "approved" is treated as a rejection.

    decision = state.get(
        "manager_decision"
    )


    if decision == "approved":

        return "approved"


    return "rejected"


# =========================
# Execution
# =========================

def execute_plan(state: TripCustomizationState):

    print(
        "Executing plan"
    )


    plan = state.get("plan", [])

    step = state.get("current_step", 0)


    # Every task in the plan has already been executed —
    # nothing left to do.
    if step >= len(plan):

        return {

            "execution_status": "completed"

        }


    current_task = plan[step]["task"]


    # Simulation:
    # Only the hotel reservation step depends on the external
    # service (checked in the waiting loop). Every other task in
    # the plan is treated as succeeding immediately. On the very
    # first attempt at reserve_hotel the service hasn't been
    # checked yet, so it starts out unavailable and triggers the
    # failure path.
    if current_task == "reserve_hotel":

        service_status = state.get(
            "service_status",
            "waiting"
        )

        hotel_api_available = (
            service_status == "ready"
        )


        if not hotel_api_available:


            return {


                "execution_status": "failed",


                "failed_task": current_task,


                "current_task": current_task,


                "failure_reason":
                    "Hotel API Timeout"

            }


    # This task succeeded — record it and move the plan pointer
    # to the next task so the graph knows exactly where it is.
    completed_tasks = state.get(
        "completed_tasks",
        []
    ) + [current_task]

    next_step = step + 1

    is_last_task = next_step >= len(plan)


    return {

        "execution_status":
            "completed" if is_last_task else "in_progress",

        "current_task": current_task,

        "completed_task": current_task,

        "completed_tasks": completed_tasks,

        "current_step": next_step

    }

#========================
# Completion Check
#========================

def verify_completion(state):

    tasks = state.get(
        "plan",
        []
    )

    completed = state.get(
        "completed_tasks",
        []
    )

    if len(completed)==len(tasks):
        return {"status": "complete"}

    return "continue"


# =========================
# Finalization
# =========================


def update_booking(
    state: TripCustomizationState
):

    print(
        "Updating booking status"
    )


    # A real system would already have a booking_id from the
    # reservation step; keep any existing one, otherwise assign
    # one now so downstream steps have something to key on.
    booking_id = (
        state.get("booking_id")
        or str(uuid4())[:8]
    )


    return {

    "booking_id": booking_id,

    "booking_status":"CONFIRMED",

    "confirmed_services":
        state.get(
            "completed_tasks",
            []
        )
    }



def update_database(
    state: TripCustomizationState
):

    print(
        "Updating database"
    )


    booking_id = state.get(
        "booking_id"
    )


    # Later:
    # UPDATE bookings
    # SET status='CONFIRMED'
    # WHERE booking_id=%s
    print(
        f"Booking ID: {booking_id}"
    )


    return {

        "database_status":
            "updated"

    }



def generate_final_response(
    state: TripCustomizationState
):

    print(
        "Generating final response"
    )


    response = f"""
        Your VIP trip has been confirmed.

        Booking ID:
        {state.get("booking_id")}

        Completed services:
        {state.get("completed_tasks")}
        """


    return {

        "final_response":
            response,

        "status":
            "completed"

    }

# =========================
# Failure Recovery
# =========================


def handle_failure(state: TripCustomizationState):

    print(
        "Handling execution failure"
    )


    failed_task = state.get(
        "failed_task"
    )


    reason = state.get(
        "failure_reason"
    )


    print(
        f"Failure in {failed_task}"
    )


    print(
        f"Reason: {reason}"
    )


    # Create support ticket
    ticket_id = str(uuid4())[:8]


    print(
        "=============================="
    )

    print(
        f"Ticket ID : {ticket_id}"
    )

    print(
        "Status    : OPEN"
    )

    print(
        f"Reason    : {reason}"
    )

    print(
        "Checkpoint: failure_handler"
    )

    print(
        "=============================="
    )


    return {

        "ticket_id": ticket_id,

        "ticket_status": "OPEN",

        "current_checkpoint": "failure_handler",

        "execution_status": "waiting",

        "service_status": "waiting"

    }


def update_ticket_status(
    state: TripCustomizationState,
    status: str
):

    print(
        f"Ticket {state.get('ticket_id')} -> {status}"
    )

    return {

        "ticket_status": status

    }

# =========================
# Waiting State
# =========================


def waiting_node(state: TripCustomizationState):

    print(
        "Waiting external service"
    )


    checks = state.get("waiting_checks", 0) + 1


    # Simulation:
    # Pretend the external hotel service comes back online
    # after a few status checks, instead of never recovering.
    service_ready = checks >= 3
    ticket_status = (
        "RESOLVED"
        if service_ready
        else "INVESTIGATING"
    )


    return {

        "service_status":
            "ready" if service_ready else "waiting",

        "execution_status":
            "waiting",

        "waiting_checks":
            checks,

        "ticket_status":
            ticket_status

    }



def wait_service(state: TripCustomizationState):

    print(
        "Checking external service"
    )


    # Replace later:
    # API status check


    service_ready = state.get("service_status") == "ready"


    if service_ready:

        return "continue"


    return "wait"



# =========================
# Execution Status Decision
# =========================

def check_execution_status(
    state: TripCustomizationState
):


    status = state.get(
        "execution_status"
    )


    if status == "failed":

        return "failure"



    if status == "completed":

        return {"status": "complete"}



    if status == "waiting":

        return "waiting"



    return "execute"

# =========================
# Build Graph
# =========================


workflow = StateGraph(
    TripCustomizationState
)



# Nodes

workflow.add_node(
    "receive_request",
    receive_request
)


workflow.add_node(
    "validate_customer",
    validate_customer
)


workflow.add_node(
    "analyze_request",
    analyze_request
)


workflow.add_node(
    "planning",
    run_planning
)


workflow.add_node(
    "human_approval",
    human_approval
)


workflow.add_node(
    "execute",
    execute_plan
)

workflow.add_node(
    "verify_completion",
    verify_completion
)


workflow.add_node(
    "waiting",
    waiting_node
)

workflow.add_node(

    "failure_handler",
    handle_failure

)

workflow.add_node(
    "update_booking",
    update_booking
)


workflow.add_node(
    "update_database",
    update_database
)


workflow.add_node(
    "generate_final_response",
    generate_final_response
)

# Entry

workflow.set_entry_point(
    "receive_request"
)



# Edges


workflow.add_edge(
    "receive_request",
    "validate_customer"
)



workflow.add_conditional_edges(

    "validate_customer",

    check_vip,

    {

        "vip": "analyze_request",

        "reject": END

    }

)

workflow.add_edge(
    "analyze_request",
    "planning"
)

workflow.add_edge(
    "update_booking",
    "update_database"
)


workflow.add_edge(
    "update_database",
    "generate_final_response"
)


workflow.add_edge(
    "generate_final_response",
    END
)


workflow.add_conditional_edges(

    "planning",

    evaluate_discount_policy,

    {

        "approval":
            "human_approval",

        "execute":
            "execute"

    }

)



workflow.add_conditional_edges(

    "human_approval",

    check_manager_decision,

    {

        "approved":
            "execute",

        "rejected":
            END

    }

)


workflow.add_conditional_edges(

    "execute",

    check_execution_status,

    {

        "failure":
            "failure_handler",

        "waiting":
            "waiting",

        "execute":
            "execute",

        "complete":
            "verify_completion"

    }

)

workflow.add_conditional_edges(

    "verify_completion",

    verify_completion,

    {

        "continue":
            "execute",

        "complete":
            "update_booking"

    }

)



workflow.add_conditional_edges(

    "waiting",

    wait_service,

    {

        "wait": "waiting",

        "continue": "execute"

    }

)



# =========================
# Failure Recovery Edge
# =========================


workflow.add_edge(

    "failure_handler",

    "waiting"

)



# =========================
# Checkpoint
# =========================


memory = MemorySaver()



vip_trip_graph = workflow.compile(
    checkpointer=memory
)


'''
START

 |
 v

receive_request

 |
 v

validate_customer

 |
 v

check_vip

 |----------------|
VIP             Reject
 |                |
 v                v

analyze_request   END

 |
 v

planning

 |
 v

evaluate_discount_policy

 |---------------------|
execute              human_approval
                       |
                    interrupt()
                       |
                       v
              check_manager_decision

              |--------------|
          approved        rejected
              |              |
              v              v

           execute          END


execute
   |
   |
   | failure
   v

failure_handler

   |
   v

waiting

   |
   v

wait_service

 |-------------|
wait       continue
 |             |
 v             v

waiting      execute



execute
   |
   | completed
   v

verify_completion

 |-------------|
continue   complete
   |          |
   v          v

execute   update_booking

              |
              v

       update_database

              |
              v

    generate_final_response

              |
              v

             END
'''


# =========================
# Demo: real checkpoint / resume with a fixed thread_id
# =========================
#
# This block only runs when the file is executed directly
# (`python vip_trip_customization.py`), never on import. It's
# here to prove the graph actually resumes from the saved
# checkpoint instead of restarting from scratch — the same
# thread_id is reused for both calls, and Command(resume=...)
# is what wakes the paused interrupt() back up.

if __name__ == "__main__":

    from langgraph.types import Command

    config = {

        "configurable": {

            "thread_id": "vip_trip_001"

        }

    }

    print(">>> First run: starts fresh, pauses at human_approval")

    state_after_pause = vip_trip_graph.invoke(
        {"customer_id": "C-001"},
        config
    )

    if "__interrupt__" in state_after_pause:

        payload = state_after_pause["__interrupt__"][0].value

        print()
        print("Graph paused. Interrupt payload:")
        print(payload)

    print()
    print(">>> Resuming from the SAME thread_id — not restarting")

    final_state = vip_trip_graph.invoke(
        Command(resume="approved"),
        config
    )

    print()
    print("Final state:")

    for key, value in final_state.items():

        print(f"  {key}: {value}")
