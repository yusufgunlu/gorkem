from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.base import CheckDirection, CheckStatus
from app.models.check import Check
from app.schemas.check import CheckCreate, CheckRead, CheckUpdate

router = APIRouter(prefix="/checks", tags=["Çekler"])


@router.get("", response_model=list[CheckRead])
def list_checks(
    db: Session = Depends(get_db),
    account_id: int | None = None,
    direction: CheckDirection | None = None,
    status: CheckStatus | None = None,
) -> list[CheckRead]:
    stmt = select(Check)
    if account_id is not None:
        stmt = stmt.where(Check.account_id == account_id)
    if direction is not None:
        stmt = stmt.where(Check.direction == direction)
    if status is not None:
        stmt = stmt.where(Check.status == status)
    stmt = stmt.order_by(Check.due_date)
    return list(db.scalars(stmt).all())


@router.post("", response_model=CheckRead, status_code=201)
def create_check(payload: CheckCreate, db: Session = Depends(get_db)) -> CheckRead:
    check = Check(**payload.model_dump())
    db.add(check)
    db.commit()
    db.refresh(check)
    return check


@router.get("/{check_id}", response_model=CheckRead)
def get_check(check_id: int, db: Session = Depends(get_db)) -> CheckRead:
    check = db.get(Check, check_id)
    if check is None:
        raise HTTPException(status_code=404, detail="Çek bulunamadı.")
    return check


@router.put("/{check_id}", response_model=CheckRead)
def update_check(check_id: int, payload: CheckUpdate, db: Session = Depends(get_db)) -> CheckRead:
    check = db.get(Check, check_id)
    if check is None:
        raise HTTPException(status_code=404, detail="Çek bulunamadı.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(check, field, value)
    db.commit()
    db.refresh(check)
    return check


@router.delete("/{check_id}", status_code=204)
def delete_check(check_id: int, db: Session = Depends(get_db)) -> None:
    check = db.get(Check, check_id)
    if check is None:
        raise HTTPException(status_code=404, detail="Çek bulunamadı.")
    db.delete(check)
    db.commit()
