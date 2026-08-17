from typing import Any


class TravelEnvironment:


    def __init__(
        self,
        database
    ):

        self.database = database



    def check(
        self,
        node,
        result
    ) -> dict[str, bool]:
        """
        Evaluate node using real environment feedback.
        """

        feedback = {}


        # Check flight availability
        if node.tool == "search_flights":

            feedback["flight_exists"] = (
                result is not None
                and len(result) > 0
            )


        # Check booking policy
        feedback["policy_valid"] = (
            self.check_policy(
                node,
                result
            )
        )


        # Check seat availability
        feedback["seat_available"] = (
            self.check_seats(
                result
            )
        )


        return feedback



    def check_policy(
        self,
        node,
        result
    ) -> bool:

        # Example:
        # VIP customer rules
        # cancellation rules
        # refund rules

        return True



    def check_seats(
        self,
        result
    ) -> bool:

        if not result:
            return False


        # Example:
        # result from search_flights tool
        # contains available seats

        return result.get(
            "available_seats",
            0
        ) > 0
