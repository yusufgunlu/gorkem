import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.base import TransactionStatus, TransactionType
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionRead, TransactionUpdate

router = APIRouter(prefix="/transactions", tags=["Gelir/Gider"])


@router.get("", response_model=list[TransactionRead])
def list_transactions(
    db: Session = Depends(get_db),
    account_id: int | None = None,
    transaction_type: TransactionType | None = None,
    status: TransactionStatus | None = None,
    due_before: datetime.date | None = Query(None, description="Bu tarihe kadar vadesi olanlar"),
) -> list[TransactionRead]:
    stmt = select(Transaction)
    if account_id is not None:
        stmt = stmt.where(Transaction.account_id == account_id)
    if transaction_type is not None:
        stmt = stmt.where(Transaction.transaction_type == transaction_type)
    if status is not None:
        stmt = stmt.where(Transaction.status == status)
    if due_before is not None:
        stmt = stmt.where(Transaction.due_date <= due_before)
    stmt = stmt.order_by(Transaction.due_date)
    return list(db.scalars(stmt).all())


@router.post("", response_model=TransactionRead, status_code=201)
def create_transaction(
    payload: TransactionCreate, db: Session = Depends(get_db)
) -> TransactionRead:
    transaction = Transaction(**payload.model_dump())
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@router.get("/{transaction_id}", response_model=TransactionRead)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)) -> TransactionRead:
    transaction = db.get(Transaction, transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Hareket bulunamadı.")
    return transaction


@router.put("/{transaction_id}", response_model=TransactionRead)
def update_transaction(
    transaction_id: int, payload: TransactionUpdate, db: Session = Depends(get_db)
) -> TransactionRead:
    transaction = db.get(Transaction, transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Hareket bulunamadı.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(transaction, field, value)
    db.commit()
    db.refresh(transaction)
    return transaction


@router.delete("/{transaction_id}", status_code=204)
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)) -> None:
    transaction = db.get(Transaction, transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Hareket bulunamadı.")
    db.delete(transaction)
    db.commit()
