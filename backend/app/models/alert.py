from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Alert(Base):
    """Alerte : changement d'état d'un capteur (ESP) ou détection de l'IA."""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)

    device_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)

    # esp = capteur du boîtier, ml = détection d'anomalies, vision = caméra
    source: Mapped[str] = mapped_column(String(20), nullable=False)

    # PIR, GAS, ANOMALY, INTRUSION
    type: Mapped[str] = mapped_column(String(30), index=True, nullable=False)

    # TRIGGERED ou CLEARED
    state: Mapped[str] = mapped_column(String(20), nullable=False)

    value: Mapped[float | None] = mapped_column(Float, nullable=True)

    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Date AVEC fuseau horaire : le navigateur affiche la bonne heure locale
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
