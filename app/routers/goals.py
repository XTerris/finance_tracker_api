from fastapi import Depends, Response, status, HTTPException, APIRouter
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas, oauth2
from ..database import get_db


router = APIRouter(prefix="/goals", tags=["Goals"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.Goal)
def create_goal(
    goal: schemas.GoalCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
):
    # Verify that the account belongs to the user
    account = db.query(models.Account).filter(models.Account.id == goal.account_id).first()
    if account == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account was not found"
        )
    if account.user_id != user.id:  # type: ignore
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    new_goal = models.Goal(**goal.model_dump())
    new_goal.user_id = user.id
    db.add(new_goal)
    db.commit()
    db.refresh(new_goal)
    return new_goal


@router.get("/{id}", response_model=schemas.Goal)
def get_goal(
    id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
):
    goal = db.query(models.Goal).filter(models.Goal.id == id).first()
    if goal == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Goal was not found"
        )
    if goal.user_id != user.id:  # type: ignore
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    return goal


@router.get("/", response_model=List[schemas.Goal])
def get_all_goals(
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
    limit: int = 100,
    completed: Optional[bool] = None,
):
    query = db.query(models.Goal).filter(models.Goal.user_id == user.id)
    
    if completed is not None:
        query = query.filter(models.Goal.is_completed == completed)
    
    goals = query.limit(limit).all()
    return goals


@router.put("/{id}", response_model=schemas.Goal)
def update_goal(
    id: int,
    updated_goal: schemas.GoalUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
):
    put_query = db.query(models.Goal).filter(models.Goal.id == id)
    goal = put_query.first()
    if goal == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Goal was not found"
        )
    if goal.user_id != user.id:  # type: ignore
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    # If updating account_id, verify the new account belongs to the user
    if updated_goal.account_id is not None:
        account = db.query(models.Account).filter(models.Account.id == updated_goal.account_id).first()
        if account == None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Account was not found"
            )
        if account.user_id != user.id:  # type: ignore
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    updated_data = updated_goal.model_dump()
    for key in list(updated_data.keys()):
        if updated_data[key] == None:
            updated_data.pop(key)
    put_query.update(updated_data, synchronize_session=False)  # type: ignore
    db.commit()
    return put_query.first()


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
):
    delete_query = db.query(models.Goal).filter(models.Goal.id == id)
    goal = delete_query.first()
    if goal == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Goal was not found"
        )
    if goal.user_id != user.id:  # type: ignore
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    delete_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{id}/complete", response_model=schemas.Goal)
def mark_goal_complete(
    id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
):
    """Mark a goal as completed"""
    put_query = db.query(models.Goal).filter(models.Goal.id == id)
    goal = put_query.first()
    if goal == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Goal was not found"
        )
    if goal.user_id != user.id:  # type: ignore
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    put_query.update({"is_completed": True}, synchronize_session=False)
    db.commit()
    return put_query.first()


@router.patch("/{id}/incomplete", response_model=schemas.Goal)
def mark_goal_incomplete(
    id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
):
    """Mark a goal as incomplete"""
    put_query = db.query(models.Goal).filter(models.Goal.id == id)
    goal = put_query.first()
    if goal == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Goal was not found"
        )
    if goal.user_id != user.id:  # type: ignore
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    put_query.update({"is_completed": False}, synchronize_session=False)
    db.commit()
    return put_query.first()