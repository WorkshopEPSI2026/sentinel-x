import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.security import (
    create_refresh_token,
    get_refresh_token_expiration,
    hash_refresh_token,
)
from app.models.refresh_token import RefreshToken


def create_refresh_token_record(
    db: Session,
    user_id: int,
    family_id: uuid.UUID | None = None,
) -> tuple[str, RefreshToken]:

    raw_token = create_refresh_token()

    token = RefreshToken(
        user_id=user_id,
        token_hash=hash_refresh_token(raw_token),
        family_id=family_id or uuid.uuid4(),
        expires_at=get_refresh_token_expiration(),
    )

    db.add(token)
    db.flush()

    return raw_token, token


def get_refresh_token(
    db: Session,
    raw_token: str,
) -> RefreshToken | None:

    token_hash = hash_refresh_token(raw_token)

    return db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash
        )
    )


def revoke_refresh_token(
    db: Session,
    token: RefreshToken,
) -> None:

    token.revoked_at = datetime.now(timezone.utc)


def revoke_token_family(
    db: Session,
    family_id: uuid.UUID,
) -> None:

    db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.family_id == family_id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(
            revoked_at=datetime.now(timezone.utc),
        )
    )


def is_refresh_token_valid(token: RefreshToken) -> bool:

    now = datetime.now(timezone.utc)

    return (
        token.revoked_at is None
        and token.expires_at > now
    )