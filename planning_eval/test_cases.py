from dataclasses import dataclass


@dataclass
class TestCase:
    id: str
    category: str
    goal: str
    expected_success: bool = True


TEST_CASES = [

    # =========================================================
    # T1 - SIMPLE / DIRECT MCP EXECUTION
    # =========================================================

    TestCase(
        id="T1",
        category="simple",
        goal=(
            "Check the current status of flight 1."
        ),
        expected_success=True,
    ),

    # =========================================================
    # T2 - SIMPLE / MULTI-TOOL INFORMATION GATHERING
    # =========================================================

    TestCase(
        id="T2",
        category="simple_multi_tool",
        goal=(
            "Check flight 2 status, determine the delay duration "
            "and disruption reason, and report the available "
            "information."
        ),
        expected_success=True,
    ),

    # =========================================================
    # T3 - COMPLEX / DECOMPOSITION + PLANNING
    # =========================================================

    TestCase(
        id="T3",
        category="complex",
        goal=(
            "Flight 2 has a 120-minute delay because of bad weather "
            "and has connection risk. Identify affected bookings, "
            "assess passenger priority, find suitable rebooking "
            "alternatives, and propose an appropriate plan."
        ),
        expected_success=True,
    ),

    # =========================================================
    # T4 - MULTI-DECISION / POLICY + ALTERNATIVES
    # =========================================================

    TestCase(
        id="T4",
        category="multi_decision",
        goal=(
            "Handle the disruption of flight 2. Identify affected "
            "customers, check their priority, evaluate alternative "
            "flights or transportation, determine applicable "
            "compensation, and produce a final recommendation "
            "consistent with company policies."
        ),
        expected_success=True,
    ),

    # =========================================================
    # T5 - FAILURE / REFLEXION / NEGATIVE CASE
    # =========================================================

    TestCase(
        id="T5",
        category="failure",
        goal=(
            "Find a valid alternative flight from CAI to JED on "
            "2099-01-01 and propose a rebooking."
        ),
        expected_success=False,
    ),
]