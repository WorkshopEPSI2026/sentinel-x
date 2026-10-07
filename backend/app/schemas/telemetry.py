from datetime import datetime

from pydantic import BaseModel


class TelemetryCreate(BaseModel):
    device_id: str
    temperature: float
    humidity: float
    gas: int
    presence: bool


class TelemetryResponse(TelemetryCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True