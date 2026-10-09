from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.alert import Alert
from app.schemas.alert import AlertCreate, AlertResponse
from app.services.alert import create_alert
from app.services.websocket import alerts_manager


router = APIRouter(
    prefix="/api/alerts",
    tags=["Alerts"],
)


def _active_alerts(db: Session) -> list[Alert]:
    """Alertes en cours : pour chaque (boîtier, type), la dernière alerte est TRIGGERED."""
    last: dict[tuple[str, str], Alert] = {}
    for alert in db.query(Alert).order_by(Alert.created_at.desc()).limit(500):
        last.setdefault((alert.device_id, alert.type), alert)
    return [a for a in last.values() if a.state == "TRIGGERED"]


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
        .limit(min(limit, 500))
        .all()
    )


@router.get(
    "/active",
    response_model=list[AlertResponse],
)
def get_active_alerts(
    db: Session = Depends(get_db),
):
    return _active_alerts(db)


@router.post(
    "/{alert_id}/resolve",
    response_model=AlertResponse,
)
async def resolve_alert_by_id(
    alert_id: int,
    db: Session = Depends(get_db),
):
    """L'opérateur acquitte une alerte : on enregistre un CLEARED pour le même boîtier et le même type."""
    alert = db.get(Alert, alert_id)

    if not alert:
        raise HTTPException(status_code=404, detail="Alerte introuvable")

    cleared = create_alert(db, AlertCreate(
        device_id=alert.device_id,
        source="operator",
        type=alert.type,
        state="CLEARED",
        value=None,
        detail={"resolved_alert_id": alert.id},
    ))

    message = AlertResponse.model_validate(cleared).model_dump(mode="json")
    await alerts_manager.broadcast(message)

    return cleared
