"""Ekstre içe aktarma akışının veritabanı ile konuşan iş mantığı.

API (`app/api/v1/statements.py`) ve web arayüzü (`app/web/routes.py`) aynı
fonksiyonları kullanır; böylece "yükle -> oku -> eşleştir -> onayla" akışı
tek bir yerde tanımlanır.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.account import Account
from app.models.base import (
    StatementFileType,
    StatementLineStatus,
    TransactionStatus,
    TransactionType,
)
from app.models.statement import StatementImport, StatementLine
from app.models.transaction import Transaction
from app.services import matcher
from app.services.statement_parser import parse_statement_file


def create_statement_import(
    db: Session, filename: str, file_bytes: bytes, bank_name: str | None = None
) -> StatementImport:
    """Dosyayı okur, satırları kaydeder ve cari hesaplarla otomatik eşleştirir."""
    settings = get_settings()
    raw_lines = parse_statement_file(filename, file_bytes)

    file_type = (
        StatementFileType.EXCEL
        if filename.lower().endswith((".xlsx", ".xls"))
        else StatementFileType.PDF
    )

    statement_import = StatementImport(
        filename=filename,
        file_type=file_type,
        bank_name=bank_name,
        total_rows=len(raw_lines),
    )
    db.add(statement_import)
    db.flush()

    accounts = list(db.scalars(select(Account)).all())
    matched_count = 0

    for raw in raw_lines:
        candidate = matcher.find_best_match(raw.description, accounts)
        matched_account_id = None
        match_confidence = None
        status = StatementLineStatus.BEKLIYOR

        if candidate is not None:
            match_confidence = candidate.score
            if candidate.score >= settings.statement_match_threshold:
                matched_account_id = candidate.account_id
                status = StatementLineStatus.ESLESTI
                matched_count += 1

        db.add(
            StatementLine(
                import_id=statement_import.id,
                transaction_date=raw.transaction_date,
                raw_description=raw.description,
                amount=raw.amount,
                balance_after=raw.balance_after,
                matched_account_id=matched_account_id,
                match_confidence=match_confidence,
                status=status,
            )
        )

    statement_import.matched_rows = matched_count
    db.commit()
    db.refresh(statement_import)
    return statement_import


def confirm_statement_line(
    db: Session, line_id: int, account_id: int, create_transaction: bool = True
) -> StatementLine:
    """Bir satırın cari eşleşmesini onaylar/düzeltir, isteğe bağlı hareket oluşturur."""
    line = db.get(StatementLine, line_id)
    if line is None:
        raise ValueError("Ekstre satırı bulunamadı.")

    account = db.get(Account, account_id)
    if account is None:
        raise ValueError("Cari hesap bulunamadı.")

    line.matched_account_id = account.id
    line.status = StatementLineStatus.MANUEL

    if create_transaction:
        transaction = Transaction(
            account_id=account.id,
            transaction_type=(
                TransactionType.GELIR if float(line.amount) >= 0 else TransactionType.GIDER
            ),
            amount=abs(float(line.amount)),
            due_date=line.transaction_date,
            paid_date=line.transaction_date,
            status=TransactionStatus.ODENDI,
            description=line.raw_description,
            source_statement_line_id=line.id,
        )
        db.add(transaction)

    db.commit()
    db.refresh(line)
    return line


def reject_statement_line(db: Session, line_id: int) -> StatementLine:
    line = db.get(StatementLine, line_id)
    if line is None:
        raise ValueError("Ekstre satırı bulunamadı.")
    line.status = StatementLineStatus.REDDEDILDI
    line.matched_account_id = None
    db.commit()
    db.refresh(line)
    return line
