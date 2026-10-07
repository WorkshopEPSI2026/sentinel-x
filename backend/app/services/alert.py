from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.schemas.alert import AlertCreate


def alert_from_mqtt(topic: str, payload: dict) -> AlertCreate:
    """
    Convertit un message MQTT en alerte.
      sentinel/esp8266/events : {"device_id","type":"PIR|GAS","state","value"}   (ESP)
      sentinel/esp8266/alerts : {"device_id","source":"ml","type":"ANOMALY","state","score","detail"} (IA)
    """
    source = payload.get("source") or ("esp" if topic.endswith("/events") else "ml")
    value = payload.get("value", payload.get("score"))

    return AlertCreate(
        device_id=payload.get("device_id", "inconnu"),
        source=source,
        type=str(payload["type"]).upper(),
        state=str(payload["state"]).upper(),
        value=float(value) if value is not None else None,
        detail=payload.get("detail"),
    )


def create_alert(db: Session, alert: AlertCreate) -> Alert:
    db_alert = Alert(**alert.model_dump())

    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)

    return db_alert
