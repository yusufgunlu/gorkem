from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.account import Account
from app.schemas.account import AccountCreate, AccountRead, AccountUpdate

router = APIRouter(prefix="/accounts", tags=["Cari Hesaplar"])


def _current_balance(account: Account) -> float:
    balance = float(account.opening_balance)
    for tx in account.transactions:
        if tx.transaction_type.value == "gelir":
            balance += float(tx.amount)
        else:
            balance -= float(tx.amount)
    return balance


def _to_read(account: Account) -> AccountRead:
    data = AccountRead.model_validate(account)
    data.current_balance = _current_balance(account)
    return data


@router.get("", response_model=list[AccountRead])
def list_accounts(db: Session = Depends(get_db)) -> list[AccountRead]:
    accounts = db.scalars(select(Account).order_by(Account.name)).all()
    return [_to_read(a) for a in accounts]


@router.post("", response_model=AccountRead, status_code=201)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)) -> AccountRead:
    account = Account(**payload.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return _to_read(account)


@router.get("/{account_id}", response_model=AccountRead)
def get_account(account_id: int, db: Session = Depends(get_db)) -> AccountRead:
    account = db.get(Account, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Cari hesap bulunamadı.")
    return _to_read(account)


@router.put("/{account_id}", response_model=AccountRead)
def update_account(
    account_id: int, payload: AccountUpdate, db: Session = Depends(get_db)
) -> AccountRead:
    account = db.get(Account, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Cari hesap bulunamadı.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(account, field, value)
    db.commit()
    db.refresh(account)
    return _to_read(account)


@router.delete("/{account_id}", status_code=204)
def delete_account(account_id: int, db: Session = Depends(get_db)) -> None:
    account = db.get(Account, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Cari hesap bulunamadı.")
    db.delete(account)
    db.commit()
