from pydantic import BaseModel, Field, ConfigDict


class FlightIdInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    flight_id: int = Field(
        ...,
        description="Unique flight identifier.",
        ge=1,
    )


class AirportCodeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    airport_code: str = Field(
        ...,
        description="Three-letter IATA airport code.",
        min_length=3,
        max_length=3,
    )


class DestinationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    destination: str = Field(
        ...,
        description="Destination airport IATA code.",
        min_length=3,
        max_length=3,
    )
