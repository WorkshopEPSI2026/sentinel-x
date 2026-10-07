from sqlalchemy.orm import Session

from app.models.telemetry import Telemetry
from app.schemas.telemetry import TelemetryCreate


def create_telemetry(
    db: Session,
    telemetry: TelemetryCreate,
) -> Telemetry:
    db_telemetry = Telemetry(
        device_id=telemetry.device_id,
        temperature=telemetry.temperature,
        humidity=telemetry.humidity,
        gas=telemetry.gas,
        presence=telemetry.presence,
    )

    db.add(db_telemetry)
    db.commit()
    db.refresh(db_telemetry)

    return db_telemetry