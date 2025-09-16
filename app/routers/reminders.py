from fastapi import Depends, Response, status, HTTPException, APIRouter
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas, oauth2
from ..database import get_db


router = APIRouter(prefix="/reminders", tags=["Reminders"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.Reminder)
def create_reminder(
    reminder: schemas.ReminderCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
):
    new_reminder = models.Reminder(**reminder.model_dump())
    new_reminder.user_id = user.id
    db.add(new_reminder)
    db.commit()
    db.refresh(new_reminder)
    return new_reminder


@router.get("/{id}", response_model=schemas.Reminder)
def get_reminder(
    id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
):
    reminder = db.query(models.Reminder).filter(models.Reminder.id == id).first()
    if reminder == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reminder was not found"
        )
    if reminder.user_id != user.id:  # type: ignore
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    return reminder


@router.get("/", response_model=List[schemas.Reminder])
def get_all_reminders(
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
    limit: int = 100,
    active: Optional[bool] = None,
):
    query = db.query(models.Reminder).filter(models.Reminder.user_id == user.id)
    
    if active is not None:
        query = query.filter(models.Reminder.is_active == active)
    
    reminders = query.limit(limit).all()
    return reminders


@router.put("/{id}", response_model=schemas.Reminder)
def update_reminder(
    id: int,
    updated_reminder: schemas.ReminderUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
):
    put_query = db.query(models.Reminder).filter(models.Reminder.id == id)
    reminder = put_query.first()
    if reminder == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reminder was not found"
        )
    if reminder.user_id != user.id:  # type: ignore
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    updated_data = updated_reminder.model_dump()
    for key in list(updated_data.keys()):
        if updated_data[key] == None:
            updated_data.pop(key)
    put_query.update(updated_data, synchronize_session=False)  # type: ignore
    db.commit()
    return put_query.first()


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder(
    id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
):
    delete_query = db.query(models.Reminder).filter(models.Reminder.id == id)
    reminder = delete_query.first()
    if reminder == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reminder was not found"
        )
    if reminder.user_id != user.id:  # type: ignore
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    delete_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{id}/activate", response_model=schemas.Reminder)
def activate_reminder(
    id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
):
    """Activate a reminder"""
    put_query = db.query(models.Reminder).filter(models.Reminder.id == id)
    reminder = put_query.first()
    if reminder == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reminder was not found"
        )
    if reminder.user_id != user.id:  # type: ignore
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    put_query.update({"is_active": True}, synchronize_session=False)
    db.commit()
    return put_query.first()


@router.patch("/{id}/deactivate", response_model=schemas.Reminder)
def deactivate_reminder(
    id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
):
    """Deactivate a reminder"""
    put_query = db.query(models.Reminder).filter(models.Reminder.id == id)
    reminder = put_query.first()
    if reminder == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reminder was not found"
        )
    if reminder.user_id != user.id:  # type: ignore
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    put_query.update({"is_active": False}, synchronize_session=False)
    db.commit()
    return put_query.first()