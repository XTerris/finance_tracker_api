from fastapi import Depends, status, HTTPException, APIRouter
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, utils, oauth2
from ..database import get_db


router = APIRouter(tags=["Authentication"])


@router.post("/login", response_model=schemas.TokenWithRefresh)
def login(
    login_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user_data = (
        db.query(models.User).filter(models.User.login == login_data.username).first()
    )
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    if not utils.verify(login_data.password, user_data.password):  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    access_token = oauth2.create_access_token(data={"user_id": user_data.id})

    refresh_token = oauth2.create_refresh_token(
        data={"user_id": user_data.id, "token_version": user_data.token_version}
    )

    user_data.refresh_token = refresh_token
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=schemas.TokenWithRefresh)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """
    Exchange a valid refresh token for a new access token and refresh token.
    This invalidates the old refresh token (token rotation).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = oauth2.verify_refresh_token(refresh_token, credentials_exception)

    user = db.query(models.User).filter(models.User.id == token_data.id).first()
    if user is None:
        raise credentials_exception

    if user.token_version != token_data.token_version:
        raise credentials_exception

    if user.refresh_token != refresh_token:
        raise credentials_exception

    user.token_version += 1

    new_access_token = oauth2.create_access_token(data={"user_id": user.id})
    new_refresh_token = oauth2.create_refresh_token(
        data={"user_id": user.id, "token_version": user.token_version}
    )

    user.refresh_token = new_refresh_token
    db.commit()

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    user: models.User = Depends(oauth2.get_current_user), db: Session = Depends(get_db)
):
    """
    Logout by invalidating the user's refresh token.
    Increments token version to invalidate all tokens.
    """
    user.refresh_token = None
    user.token_version += 1
    db.commit()

    return None
