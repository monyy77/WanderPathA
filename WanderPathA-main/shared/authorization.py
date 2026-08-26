from shared.validation import employee_exists


def manager_required(employee_id: int):

    employee = employee_exists(employee_id)

    if employee["role"] != "Manager":
        raise PermissionError(
            "Only managers can perform this action."
        )

    return employee


from shared.validation import employee_exists


def admin_required(employee_id: int):

    employee = employee_exists(employee_id)

    if employee["role"] != "Admin":
        raise PermissionError(
            "Only admins can perform this action."
        )

    return employee

from shared.validation import employee_exists


def support_or_higher(employee_id: int):

    employee = employee_exists(employee_id)

    allowed = {
        "Support Agent",
        "Supervisor",
        "Manager",
        "Admin",
    }

    if employee["role"] not in allowed:
        raise PermissionError(
            "Access denied."
        )

    return employee
