from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.alert import Alert
from app.schemas.alert import AlertResponse


router = APIRouter(
    prefix="/api/alerts",
    tags=["Alerts"],
)


@router.get(
    "",
    response_model=list[AlertResponse],
)
def get_alerts(
    limit: int = 50,
    db: Session = Depends(get_db),
):

    return (
        db.query(Alert)
        .order_by(Alert.created_at.desc())
        .limit(limit)
        .all()
    )


@router.get(
    "/active",
    response_model=list[AlertResponse],
)
def get_active_alerts(
    db: Session = Depends(get_db),
):

    return (
        db.query(Alert)
        .filter(Alert.status == "active")
        .order_by(Alert.created_at.desc())
        .all()
    )


@router.post(
    "/{alert_id}/resolve",
    response_model=AlertResponse,
)
def resolve_alert_by_id(
    alert_id: int,
    db: Session = Depends(get_db),
):

    alert = (
        db.query(Alert)
        .filter(Alert.id == alert_id)
        .first()
    )

    if not alert:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail="Alerte introuvable",
        )

    alert.status = "resolved"

    from datetime import datetime, timezone

    alert.resolved_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(alert)

    return alert