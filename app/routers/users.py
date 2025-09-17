from fastapi import Depends, Response, status, HTTPException, APIRouter
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, utils, oauth2
from ..database import get_db



router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=schemas.User)
def get_current_user(user: models.User = Depends(oauth2.get_current_user)):
    return user


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    user.password = utils.hash(user.password)
    new_user = models.User(**user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/{id}", response_model=schemas.User)
def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id).first()
    if user:
        return user
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="User was not found"
    )


@router.get("/", response_model=List[schemas.User])
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return users


@router.put("/", response_model=schemas.User)
def update_user(
    updated_user: schemas.UserUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
):
    if updated_user.password is not None:
        updated_user.password = utils.hash(updated_user.password)
    put_query = db.query(models.User).filter(models.User.id == user.id)
    user = put_query.first()
    updated_data = updated_user.model_dump()
    for i in list(updated_data.keys()):
        if updated_data[i] == None:
            updated_data.pop(i)
    put_query.update(updated_data, synchronize_session=False)  # type: ignore
    db.commit()
    return put_query.first()


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    db: Session = Depends(get_db), user: models.User = Depends(oauth2.get_current_user)
):
    delete_query = db.query(models.User).filter(models.User.id == user.id)
    delete_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
