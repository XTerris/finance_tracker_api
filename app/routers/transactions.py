from fastapi import Depends, Response, status, HTTPException, APIRouter
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas, oauth2
from ..database import get_db


router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=schemas.Transaction
)
def add_transaction(
    trans: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
):
    new_trans = models.Transaction(**trans.model_dump())
    new_trans.user_id = user.id
    db.add(new_trans)
    db.commit()
    db.refresh(new_trans)
    return new_trans


@router.get("/{id}", response_model=schemas.Transaction)
def get_transaction(
    id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
):
    trans = db.query(models.Transaction).filter(models.Transaction.id == id).first()
    if trans.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    if trans:
        return trans
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Transaction was not found"
    )


@router.get("/", response_model=List[schemas.Transaction])
def get_all_transactions(
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
    limit: int = 10,
    search: Optional[str] = "",
):
    trans = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.user_id == user.id,
            models.Transaction.title.contains(search),
        )
        .limit(limit)
        .all()
    )
    return trans


@router.put("/{id}", response_model=schemas.Transaction)
def update_transaction(
    id: int,
    updated_trans: schemas.TransactionUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
):
    put_query = db.query(models.Transaction).filter(models.Transaction.id == id)
    trans = put_query.first()
    if trans == None:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction was not found"
        )
    if trans.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    put_query.update(updated_trans.model_dump(), synchronize_session=False)
    db.commit()
    return put_query.first()


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
):
    delete_query = db.query(models.Transaction).filter(models.Transaction.id == id)
    if delete_query.first() == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction was not found"
        )
    if delete_query.first().user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    delete_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
