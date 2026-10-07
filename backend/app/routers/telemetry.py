from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.telemetry import Telemetry
from app.schemas.telemetry import TelemetryResponse


router = APIRouter(
    prefix="/api/telemetry",
    tags=["Telemetry"],
)


@router.get("/latest", response_model=TelemetryResponse)
def get_latest_telemetry(
    db: Session = Depends(get_db),
):
    telemetry = (
        db.query(Telemetry)
        .order_by(Telemetry.created_at.desc())
        .first()
    )

    return telemetry

@router.get("/history", response_model=list[TelemetryResponse])
def get_telemetry_history(
    limit: int = 50,
    db: Session = Depends(get_db),
):
    telemetry = (
        db.query(Telemetry)
        .order_by(Telemetry.created_at.desc())
        .limit(limit)
        .all()
    )

    return telemetry