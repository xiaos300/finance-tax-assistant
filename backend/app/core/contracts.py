"""D0 subset of contracts 1.2. Expand only alongside implemented features."""
from typing import Annotated, Generic, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

Id = Annotated[str, Field(min_length=1, max_length=128)]
Version = Annotated[int, Field(ge=1)]
Revision = Annotated[int, Field(ge=0)]
T = TypeVar("T")


class Contract(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


class Health(Contract):
    status: Literal["alive", "ready", "not_ready"]
    checks: dict[str, bool] = Field(default_factory=dict)


class Envelope(Contract, Generic[T]):
    data: T
    request_id: Id


class ErrorBody(Contract):
    code: Id
    message: Annotated[str, Field(min_length=1, max_length=1000)]
    details: dict[str, object]
    retryable: bool
    turn_id: UUID | None


class ErrorEnvelope(Contract):
    error: ErrorBody
    request_id: Id
