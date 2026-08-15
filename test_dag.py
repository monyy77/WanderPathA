import sys
 
from planning.dag import Plan, Task, TaskType
 
PASSED = 0
FAILED = 0
 
 
def check(label: str, condition: bool) -> None:
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"[PASS] {label}")
    else:
        FAILED += 1
        print(f"[FAIL] {label}")
 
 
def test_valid_plan_builds_and_batches_correctly() -> None:
    plan = Plan(
        goal="Reshuffle bookings for a disrupted flight",
        tasks=[
            Task(
                id="t1",
                instruction="get disruption info",
                kind=TaskType.TOOL_CALL,
                tool_name="get_flight_status",
            ),
            Task(
                id="t2",
                instruction="get affected bookings",
                kind=TaskType.TOOL_CALL,
                tool_name="get_bookings_by_flight",
            ),
            Task(id="t3", instruction="assess priority", depends_on=["t1", "t2"]),
            Task(id="t7", instruction="synthesize final plan", depends_on=["t3"]),
        ],
    )
    check("valid plan builds without error", True)
    check(
        "independent lookups (t1, t2) share the first batch",
        plan.execution_batches()[0] == ["t1", "t2"],
    )
    check(
        "dependent task (t3) runs only after its dependencies",
        plan.execution_batches()[1] == ["t3"],
    )
    check("terminal task is correctly detected", plan.terminal_tasks() == ["t7"])
 
 
def test_cycle_is_rejected_at_construction_time() -> None:
    try:
        Plan(
            goal="Broken cyclic plan for testing",
            tasks=[
                Task(id="a", instruction="depends on b", depends_on=["b"]),
                Task(id="b", instruction="depends on a", depends_on=["a"]),
            ],
        )
        check("cycle is rejected", False)
    except Exception:
        check("cycle is rejected", True)
 
 
def test_tool_call_without_tool_name_is_rejected() -> None:
    try:
        Plan(
            goal="Missing tool name for testing",
            tasks=[
                Task(id="t1", instruction="do a tool call", kind=TaskType.TOOL_CALL),
            ],
        )
        check("tool_call without tool_name is rejected", False)
    except Exception:
        check("tool_call without tool_name is rejected", True)
 
 
def test_duplicate_task_ids_are_rejected() -> None:
    try:
        Plan(
            goal="Duplicate ids for testing",
            tasks=[
                Task(id="t1", instruction="first task here"),
                Task(id="t1", instruction="second task here"),
            ],
        )
        check("duplicate task ids are rejected", False)
    except Exception:
        check("duplicate task ids are rejected", True)
 
 
def test_unknown_dependency_is_rejected() -> None:
    try:
        Plan(
            goal="Unknown dependency for testing",
            tasks=[
                Task(id="t1", instruction="depends on ghost", depends_on=["ghost"]),
            ],
        )
        check("unknown dependency is rejected", False)
    except Exception:
        check("unknown dependency is rejected", True)
 
 
if __name__ == "__main__":
    print("=== Testing planning/dag.py ===\n")
    test_valid_plan_builds_and_batches_correctly()
    test_cycle_is_rejected_at_construction_time()
    test_tool_call_without_tool_name_is_rejected()
    test_duplicate_task_ids_are_rejected()
    test_unknown_dependency_is_rejected()
 
    print(f"\n{PASSED} passed, {FAILED} failed")
    sys.exit(1 if FAILED else 0)
 
