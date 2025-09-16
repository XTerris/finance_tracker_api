from fastapi import Depends, Response, status, HTTPException, APIRouter
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas, oauth2
from ..database import get_db


router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.Account)
def create_account(
    account: schemas.AccountCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
):
    new_account = models.Account(**account.model_dump())
    new_account.user_id = user.id
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return new_account


@router.get("/{id}", response_model=schemas.Account)
def get_account(
    id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
):
    account = db.query(models.Account).filter(models.Account.id == id).first()
    if account == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account was not found"
        )
    if account.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    return account


@router.get("/", response_model=List[schemas.Account])
def get_all_accounts(
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
    limit: int = 100,
    search: Optional[str] = "",
):
    accounts = (
        db.query(models.Account)
        .filter(
            models.Account.user_id == user.id,
            models.Account.name.contains(search),
        )
        .limit(limit)
        .all()
    )
    return accounts


@router.put("/{id}", response_model=schemas.Account)
def update_account(
    id: int,
    updated_account: schemas.AccountUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
):
    put_query = db.query(models.Account).filter(models.Account.id == id)
    account = put_query.first()
    if account == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account was not found"
        )
    if account.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    updated_data = updated_account.model_dump()
    for key in list(updated_data.keys()):
        if updated_data[key] == None:
            updated_data.pop(key)
    put_query.update(updated_data, synchronize_session=False)
    db.commit()
    return put_query.first()


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
):
    delete_query = db.query(models.Account).filter(models.Account.id == id)
    account = delete_query.first()
    if account == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account was not found"
        )
    if account.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    delete_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
