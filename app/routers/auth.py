from fastapi import Depends, status, HTTPException, APIRouter
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, utils, oauth2
from ..database import get_db


router = APIRouter(tags=["Authentication"])


@router.post("/login", response_model=schemas.Token)
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
    print(login_data.password, user_data.password)
    if not utils.verify(login_data.password, user_data.password):  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    access_token = oauth2.create_access_token(data={"user_id": user_data.id})

    return {"access_token": access_token, "token_type": "bearer"}
