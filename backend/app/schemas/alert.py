from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AlertCreate(BaseModel):
    device_id: str
    source: str
    type: str
    state: str
    value: float | None = None
    detail: dict[str, Any] | None = None


class AlertResponse(AlertCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
