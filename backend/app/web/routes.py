import datetime

from fastapi import APIRouter, Depends, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.account import Account
from app.models.base import AccountType, CheckDirection, CheckStatus, TransactionType
from app.models.check import Check
from app.models.statement import StatementImport
from app.models.transaction import Transaction
from app.services.cashflow import build_cashflow_report, summarize_income_expense
from app.services.statement_parser import StatementParseError
from app.services.statement_service import (
    confirm_statement_line,
    create_statement_import,
    reject_statement_line,
)

router = APIRouter(tags=["Arayüz"])
templates = Jinja2Templates(directory="app/templates")


def _account_balance(account: Account) -> float:
    balance = float(account.opening_balance)
    for tx in account.transactions:
        balance += float(tx.amount) if tx.transaction_type == TransactionType.GELIR else -float(tx.amount)
    return balance


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    accounts = list(db.scalars(select(Account)).all())
    transactions = list(db.scalars(select(Transaction)).all())
    checks = list(db.scalars(select(Check)).all())

    today = datetime.date.today()
    horizon = today + datetime.timedelta(days=30)

    upcoming_tx = sorted(
        [t for t in transactions if t.status.value != "odendi" and t.due_date <= horizon],
        key=lambda t: t.due_date,
    )[:8]
    upcoming_checks = sorted(
        [c for c in checks if c.status == CheckStatus.PORTFOY and c.due_date <= horizon],
        key=lambda c: c.due_date,
    )[:8]

    total_income, total_expense, _ = summarize_income_expense(
        transactions, today - datetime.timedelta(days=30), today
    )
    opening_balance = sum(float(a.opening_balance) for a in accounts)
    cashflow = build_cashflow_report(
        transactions, checks, opening_balance, today, today + datetime.timedelta(days=14)
    )

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "active_page": "dashboard",
            "account_count": len(accounts),
            "total_balance": sum(_account_balance(a) for a in accounts),
            "total_income_30d": total_income,
            "total_expense_30d": total_expense,
            "upcoming_tx": upcoming_tx,
            "upcoming_checks": upcoming_checks,
            "cashflow_labels": [p.date.strftime("%d.%m") for p in cashflow.points],
            "cashflow_values": [p.running_balance for p in cashflow.points],
        },
    )


@router.get("/cari", response_class=HTMLResponse)
def accounts_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    accounts = list(db.scalars(select(Account).order_by(Account.name)).all())
    rows = [
        {"account": a, "balance": _account_balance(a)} for a in accounts
    ]
    return templates.TemplateResponse(
        request,
        "accounts.html",
        {"active_page": "cari", "rows": rows, "account_types": list(AccountType)},
    )


@router.post("/cari")
def create_account_web(
    name: str = Form(...),
    account_type: AccountType = Form(AccountType.MUSTERI),
    tax_number: str = Form(""),
    iban: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    match_aliases: str = Form(""),
    opening_balance: float = Form(0),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    account = Account(
        name=name,
        account_type=account_type,
        tax_number=tax_number or None,
        iban=iban or None,
        phone=phone or None,
        email=email or None,
        match_aliases=match_aliases or None,
        opening_balance=opening_balance,
    )
    db.add(account)
    db.commit()
    return RedirectResponse(url="/cari", status_code=303)


@router.get("/cekler", response_class=HTMLResponse)
def checks_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    checks = list(db.scalars(select(Check).order_by(Check.due_date)).all())
    accounts = list(db.scalars(select(Account).order_by(Account.name)).all())
    return templates.TemplateResponse(
        request,
        "checks.html",
        {
            "active_page": "cekler",
            "checks": checks,
            "accounts": accounts,
            "directions": list(CheckDirection),
            "statuses": list(CheckStatus),
        },
    )


@router.post("/cekler")
def create_check_web(
    account_id: int = Form(...),
    direction: CheckDirection = Form(...),
    check_number: str = Form(...),
    bank_name: str = Form(""),
    amount: float = Form(...),
    issue_date: datetime.date = Form(...),
    due_date: datetime.date = Form(...),
    status: CheckStatus = Form(CheckStatus.PORTFOY),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    check = Check(
        account_id=account_id,
        direction=direction,
        check_number=check_number,
        bank_name=bank_name or None,
        amount=amount,
        issue_date=issue_date,
        due_date=due_date,
        status=status,
    )
    db.add(check)
    db.commit()
    return RedirectResponse(url="/cekler", status_code=303)


@router.get("/ekstre", response_class=HTMLResponse)
def statements_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    imports = list(
        db.scalars(select(StatementImport).order_by(StatementImport.created_at.desc())).all()
    )
    accounts = list(db.scalars(select(Account).order_by(Account.name)).all())
    return templates.TemplateResponse(
        request,
        "statement_import.html",
        {"active_page": "ekstre", "imports": imports, "accounts": accounts, "error": None},
    )


@router.post("/ekstre/upload", response_class=HTMLResponse)
async def upload_statement_web(
    request: Request, file: UploadFile, db: Session = Depends(get_db)
) -> HTMLResponse:
    error = None
    try:
        file_bytes = await file.read()
        create_statement_import(db, file.filename or "ekstre", file_bytes)
    except StatementParseError as exc:
        error = str(exc)

    imports = list(
        db.scalars(select(StatementImport).order_by(StatementImport.created_at.desc())).all()
    )
    accounts = list(db.scalars(select(Account).order_by(Account.name)).all())
    return templates.TemplateResponse(
        request,
        "statement_import.html",
        {"active_page": "ekstre", "imports": imports, "accounts": accounts, "error": error},
    )


@router.post("/ekstre/lines/{line_id}/confirm")
def confirm_line_web(
    line_id: int, account_id: int = Form(...), db: Session = Depends(get_db)
) -> RedirectResponse:
    confirm_statement_line(db, line_id, account_id, create_transaction=True)
    return RedirectResponse(url="/ekstre", status_code=303)


@router.post("/ekstre/lines/{line_id}/reject")
def reject_line_web(line_id: int, db: Session = Depends(get_db)) -> RedirectResponse:
    reject_statement_line(db, line_id)
    return RedirectResponse(url="/ekstre", status_code=303)


@router.get("/raporlar", response_class=HTMLResponse)
def reports_page(
    request: Request,
    db: Session = Depends(get_db),
    start: datetime.date | None = None,
    end: datetime.date | None = None,
) -> HTMLResponse:
    today = datetime.date.today()
    start = start or today.replace(day=1)
    end = end or today

    transactions = list(db.scalars(select(Transaction)).all())
    checks = list(db.scalars(select(Check)).all())
    accounts = list(db.scalars(select(Account)).all())

    total_income, total_expense, by_category = summarize_income_expense(transactions, start, end)
    opening_balance = sum(float(a.opening_balance) for a in accounts)
    cashflow = build_cashflow_report(transactions, checks, opening_balance, start, end)

    return templates.TemplateResponse(
        request,
        "reports.html",
        {
            "active_page": "raporlar",
            "start": start,
            "end": end,
            "total_income": total_income,
            "total_expense": total_expense,
            "net": total_income - total_expense,
            "by_category": by_category,
            "cashflow_labels": [p.date.strftime("%d.%m.%Y") for p in cashflow.points],
            "cashflow_values": [p.running_balance for p in cashflow.points],
        },
    )
