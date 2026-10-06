from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core import audit
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse
from app.services.audit_logs import create_audit_log
from app.services.refresh_tokens import (
    create_refresh_token_record,
    get_refresh_token,
    is_refresh_token_valid,
    revoke_refresh_token,
    revoke_token_family,
)


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


#########################################
#               REGISTER                #
#########################################
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    existing_user = db.scalar(
        select(User).where(
            or_(
                User.email == data.email,
                User.username == data.username,
            )
        )
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username already registered",
        )

    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
    )

    db.add(user)
    db.flush()

    create_audit_log(
        db=db,
        action=audit.REGISTER,
        user_id=user.id,
        resource_type="user",
        resource_id=user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    db.commit()
    db.refresh(user)

    return user


#########################################
#               LOGIN                   #
#########################################
@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    user = db.scalar(
        select(User).where(User.email == data.email)
    )

    if not user or not verify_password(
        data.password,
        user.password_hash,
    ):
        create_audit_log(
            db=db,
            action=audit.LOGIN_FAILED,
            resource_type="auth",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not user.is_active:
        create_audit_log(
            db=db,
            action=audit.LOGIN_FAILED,
            user_id=user.id,
            resource_type="auth",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    access_token = create_access_token(user.id)

    refresh_token, _ = create_refresh_token_record(
        db=db,
        user_id=user.id,
    )

    create_audit_log(
        db=db,
        action=audit.LOGIN,
        user_id=user.id,
        resource_type="auth",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


#########################################
#                  ME                   #
#########################################
@router.get(
    "/me",
    response_model=UserResponse,
)
def me(
    current_user: User = Depends(get_current_user),
):
    return current_user


#########################################
#                REFRESH                #
#########################################
@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh_token(
    data: RefreshRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    token = get_refresh_token(
        db,
        data.refresh_token,
    )

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Un token déjà révoqué est potentiellement réutilisé.
    if token.revoked_at is not None:
        revoke_token_family(
            db,
            token.family_id,
        )

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token reuse detected",
        )

    if not is_refresh_token_valid(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    user = db.get(
        User,
        token.user_id,
    )

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Révocation du token utilisé
    revoke_refresh_token(
        db,
        token,
    )

    # Création du nouveau token dans la même famille
    new_refresh_token, new_token_record = create_refresh_token_record(
        db=db,
        user_id=user.id,
        family_id=token.family_id,
    )

    token.replaced_by_id = new_token_record.id

    new_access_token = create_access_token(
        user.id,
    )

    create_audit_log(
        db=db,
        action=audit.TOKEN_REFRESH,
        user_id=user.id,
        resource_type="auth",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    db.commit()

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
    )


#########################################
#                LOGOUT                 #
#########################################
@router.post("/logout")
def logout(
    data: RefreshRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    token = get_refresh_token(
        db,
        data.refresh_token,
    )

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if token.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token already revoked",
        )

    revoke_refresh_token(
        db,
        token,
    )

    create_audit_log(
        db=db,
        action=audit.LOGOUT,
        user_id=token.user_id,
        resource_type="auth",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    db.commit()

    return {
        "message": "Successfully logged out",
    }