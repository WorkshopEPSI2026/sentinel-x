from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.alert import Alert
from app.schemas.alert import AlertResponse


router = APIRouter(
    prefix="/api/alerts",
    tags=["Alerts"],
)


@router.get("", response_model=list[AlertResponse])
def get_alerts(
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Dernières alertes, de la plus récente à la plus ancienne."""
    return (
        db.query(Alert)
        .order_by(Alert.created_at.desc())
        .limit(min(limit, 500))
        .all()
    )
