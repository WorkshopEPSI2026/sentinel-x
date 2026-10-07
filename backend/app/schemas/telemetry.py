from datetime import datetime, timezone

from pydantic import BaseModel, field_serializer


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

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        # La base stocke l'heure UTC sans fuseau : on l'indique explicitement,
        # sinon le navigateur la prend pour une heure locale (courbes décalées).
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()