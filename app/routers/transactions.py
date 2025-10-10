from fastapi import Depends, Response, status, HTTPException, APIRouter, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc, and_, func
from typing import List, Optional
from datetime import datetime, timezone
from .. import models, schemas, oauth2
from ..database import get_db


router = APIRouter(prefix="/transactions", tags=["Transactions"])


def validate_category_access(category_id: int, user_id: int, db: Session):
    """Validate that the user can access the specified category"""
    category = (
        db.query(models.Category).filter(models.Category.id == category_id).first()
    )
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category was not found"
        )
    # Allow access to system categories (user_id is None) or user's own categories
    if category.user_id is not None and category.user_id != user_id:  # type: ignore
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    return category


def validate_account_access(account_id: int, user_id: int, db: Session):
    """Validate that the user can access the specified account"""
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account was not found"
        )
    # Only allow access to user's own accounts
    if account.user_id != user_id:  # type: ignore
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    return account


@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=schemas.Transaction
)
def add_transaction(
    trans: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
):
    # Validate category access
    validate_category_access(trans.category_id, user.id, db)  # type: ignore

    # Validate account access
    validate_account_access(trans.account_id, user.id, db)  # type: ignore

    new_trans = models.Transaction(**trans.model_dump())
    new_trans.user_id = user.id
    db.add(new_trans)
    db.commit()
    db.refresh(new_trans)
    return new_trans


@router.get("/updated", response_model=List[int])
def get_updated_transactions_since(
    updated_since: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
):
    try:
        updated_since = datetime.fromtimestamp(updated_since)  # type: ignore
        updated_ids = (
            db.query(models.Transaction.id)
            .filter(
                models.Transaction.user_id == user.id,
                models.Transaction.updated_at >= updated_since,
            )
            .order_by(models.Transaction.updated_at.asc(), models.Transaction.id.asc())
            .all()
        )
    except Exception as e:
        import logging

        log = logging.getLogger("uvicorn.error")
        log.error(e)
        return []

    return [row[0] for row in updated_ids]


@router.get("/filter", response_model=List[int])
def get_transactions_by_filter(
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    account_id: Optional[int] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
):
    # Build filter conditions
    filters = [models.Transaction.user_id == user.id]

    # Text search in title
    if search:
        filters.append(models.Transaction.title.contains(search))

    # Category filter
    if category_id is not None:
        validate_category_access(category_id, user.id, db)  # type: ignore
        filters.append(models.Transaction.category_id == category_id)

    # Account filter
    if account_id is not None:
        validate_account_access(account_id, user.id, db)  # type: ignore
        filters.append(models.Transaction.account_id == account_id)

    # Date range filters
    if from_date is not None:
        filters.append(models.Transaction.done_at >= from_date)
    if to_date is not None:
        filters.append(models.Transaction.done_at <= to_date)

    # Amount range filters
    if min_amount is not None:
        filters.append(models.Transaction.amount >= min_amount)
    if max_amount is not None:
        filters.append(models.Transaction.amount <= max_amount)

    # Get transaction IDs matching filters
    transaction_ids = (
        db.query(models.Transaction.id)
        .filter(and_(*filters))
        .filter(models.Transaction.is_deleted == False)
        .order_by(models.Transaction.id)
        .all()
    )

    return [row[0] for row in transaction_ids]


@router.get("/{id}", response_model=schemas.Transaction)
def get_transaction(
    id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
):
    trans = (
        db.query(models.Transaction)
        # .options(
        #     joinedload(models.Transaction.category),
        #     joinedload(models.Transaction.user),
        #     joinedload(models.Transaction.account),
        # )
        .filter(models.Transaction.id == id).first()
    )
    if trans == None or trans.is_deleted:  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction was not found"
        )
    if trans.user_id != user.id:  # type: ignore
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    return trans


@router.get("/", response_model=schemas.TransactionListResponse)
def get_all_transactions(
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
    limit: int = 50,
    offset: int = 0,
    sort_by: str = Query("done_at", pattern="^(id|title|amount|done_at)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
):
    # Build base query with user filter
    base_query = db.query(models.Transaction).filter(
        models.Transaction.user_id == user.id
    )

    # Get total count for pagination
    total = base_query.count()

    # Build query with joins for data retrieval
    query = base_query.filter(models.Transaction.is_deleted == False)
    # query = base_query.options(
    #     joinedload(models.Transaction.category),
    #     joinedload(models.Transaction.user),
    #     joinedload(models.Transaction.account),
    # )

    # Add sorting
    sort_column = getattr(models.Transaction, sort_by)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    # Apply pagination
    trans = query.offset(offset).limit(limit).all()

    # Create pagination info
    pagination = schemas.PaginationInfo(
        total=total,
        limit=limit,
        offset=offset,
        has_next=offset + limit < total,
    )

    return schemas.TransactionListResponse(
        items=[schemas.Transaction.model_validate(t) for t in trans],
        pagination=pagination,
    )


@router.put("/{id}", response_model=schemas.Transaction)
def update_transaction(
    id: int,
    updated_trans: schemas.TransactionUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
):
    put_query = db.query(models.Transaction).filter(models.Transaction.id == id)
    trans = put_query.first()
    if trans == None or trans.is_deleted:  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction was not found"
        )
    if trans.user_id != user.id:  # type: ignore
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    # If category_id is being updated, validate access
    if updated_trans.category_id is not None:
        validate_category_access(updated_trans.category_id, user.id, db)  # type: ignore

    # If account_id is being updated, validate access
    if updated_trans.account_id is not None:
        validate_account_access(updated_trans.account_id, user.id, db)  # type: ignore

    updated_data = updated_trans.model_dump()
    for key in list(updated_data.keys()):
        if updated_data[key] == None:
            updated_data.pop(key)
    updated_data["updated_at"] = datetime.now(timezone.utc)
    put_query.update(updated_data, synchronize_session=False)  # type: ignore
    db.commit()

    # Return updated transaction with relationships
    return (
        db.query(models.Transaction)
        .options(
            joinedload(models.Transaction.category),
            joinedload(models.Transaction.user),
            joinedload(models.Transaction.account),
        )
        .filter(models.Transaction.id == id)
        .first()
    )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(oauth2.get_current_user),
):
    delete_query = db.query(models.Transaction).filter(models.Transaction.id == id)
    trans = delete_query.first()
    if trans == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction was not found"
        )
    if trans.user_id != user.id:  # type: ignore
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    delete_query.update(
        {"is_deleted": True, "updated_at": datetime.now(timezone.utc)},
        synchronize_session=False,
    )
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
