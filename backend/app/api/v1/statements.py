from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.statement import StatementImport, StatementLine
from app.schemas.statement import (
    StatementImportRead,
    StatementLineConfirm,
    StatementLineReject,
)
from app.services.statement_parser import StatementParseError
from app.services.statement_service import (
    confirm_statement_line,
    create_statement_import,
    reject_statement_line,
)

router = APIRouter(prefix="/statements", tags=["Ekstre Aktarımı"])


def _line_to_read(line: StatementLine) -> dict:
    return {
        "id": line.id,
        "transaction_date": line.transaction_date,
        "raw_description": line.raw_description,
        "amount": float(line.amount),
        "balance_after": float(line.balance_after) if line.balance_after is not None else None,
        "matched_account_id": line.matched_account_id,
        "matched_account_name": line.matched_account.name if line.matched_account else None,
        "match_confidence": line.match_confidence,
        "status": line.status,
    }


def _import_to_read(statement_import: StatementImport) -> StatementImportRead:
    return StatementImportRead(
        id=statement_import.id,
        filename=statement_import.filename,
        file_type=statement_import.file_type,
        bank_name=statement_import.bank_name,
        total_rows=statement_import.total_rows,
        matched_rows=statement_import.matched_rows,
        lines=[_line_to_read(line) for line in statement_import.lines],
    )


@router.get("", response_model=list[StatementImportRead])
def list_imports(db: Session = Depends(get_db)) -> list[StatementImportRead]:
    imports = db.scalars(
        select(StatementImport).order_by(StatementImport.created_at.desc())
    ).all()
    return [_import_to_read(i) for i in imports]


@router.post("/upload", response_model=StatementImportRead, status_code=201)
async def upload_statement(
    file: UploadFile, bank_name: str | None = None, db: Session = Depends(get_db)
) -> StatementImportRead:
    """Excel/PDF ekstre dosyasını yükler, satırları okur ve cari hesaplarla
    otomatik eşleştirmeyi dener."""
    file_bytes = await file.read()
    try:
        statement_import = create_statement_import(
            db, file.filename or "ekstre", file_bytes, bank_name
        )
    except StatementParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _import_to_read(statement_import)


@router.get("/{import_id}", response_model=StatementImportRead)
def get_import(import_id: int, db: Session = Depends(get_db)) -> StatementImportRead:
    statement_import = db.get(StatementImport, import_id)
    if statement_import is None:
        raise HTTPException(status_code=404, detail="Ekstre bulunamadı.")
    return _import_to_read(statement_import)


@router.post("/lines/{line_id}/confirm")
def confirm_line(
    line_id: int, payload: StatementLineConfirm, db: Session = Depends(get_db)
) -> dict:
    """Bir ekstre satırının cari hesap eşleşmesini onaylar/düzeltir ve
    isteğe bağlı olarak otomatik gelir/gider hareketi oluşturur."""
    try:
        line = confirm_statement_line(
            db, line_id, payload.account_id, payload.create_transaction
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "line_id": line.id,
        "status": line.status,
        "transaction_id": line.source_statement_line_id,
    }


@router.post("/lines/{line_id}/reject")
def reject_line(
    line_id: int, payload: StatementLineReject, db: Session = Depends(get_db)
) -> dict:
    try:
        line = reject_statement_line(db, line_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"line_id": line.id, "status": line.status}
