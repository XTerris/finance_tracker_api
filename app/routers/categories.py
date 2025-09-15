from fastapi import Depends, Response, status, HTTPException, APIRouter
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas, oauth2
from ..database import get_db


router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=schemas.Category
)
def create_category(
    category: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
):
    new_category = models.Category(**category.model_dump())
    new_category.user_id = user.id
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category


@router.get("/{id}", response_model=schemas.Category)
def get_category(
    id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
):
    category = db.query(models.Category).filter(models.Category.id == id).first()
    if category == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category was not found"
        )
    # Allow access to system categories (user_id is None) or user's own categories
    if category.user_id is not None and category.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    return category


@router.get("/", response_model=List[schemas.Category])
def get_all_categories(
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
    limit: int = 100,
    search: Optional[str] = "",
):
    # Get both user's categories and system categories (user_id is None)
    categories = (
        db.query(models.Category)
        .filter(
            (models.Category.user_id == user.id) | (models.Category.user_id == None),
            models.Category.name.contains(search),
        )
        .limit(limit)
        .all()
    )
    return categories


@router.put("/{id}", response_model=schemas.Category)
def update_category(
    id: int,
    updated_category: schemas.CategoryUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
):
    put_query = db.query(models.Category).filter(models.Category.id == id)
    category = put_query.first()
    if category == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category was not found"
        )
    # Only allow updating user's own categories (not system categories)
    if category.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    
    updated_data = updated_category.model_dump()
    for key in list(updated_data.keys()):
        if updated_data[key] == None:
            updated_data.pop(key)
    put_query.update(updated_data, synchronize_session=False)
    db.commit()
    return put_query.first()


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
):
    delete_query = db.query(models.Category).filter(models.Category.id == id)
    category = delete_query.first()
    if category == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category was not found"
        )
    # Only allow deleting user's own categories (not system categories)
    if category.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    # Check if category is being used by any transactions
    transactions_using_category = (
        db.query(models.Transaction)
        .filter(models.Transaction.category_id == id)
        .first()
    )
    if transactions_using_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category that is being used by transactions"
        )

    delete_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
