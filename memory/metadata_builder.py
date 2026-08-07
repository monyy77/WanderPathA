class MetadataBuilder:

    @staticmethod
    def build(
        entity_type=None,
        entity_id=None,
        booking_id=None,
        flight_id=None,
        customer_id=None
    ):

        metadata = {}

        if entity_type is not None:
            metadata["entity_type"] = entity_type

        if entity_id is not None:
            metadata["entity_id"] = entity_id

        if booking_id is not None:
            metadata["booking_id"] = booking_id

        if flight_id is not None:
            metadata["flight_id"] = flight_id

        if customer_id is not None:
            metadata["customer_id"] = customer_id

        return metadata
