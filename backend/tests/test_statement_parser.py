import io

import pandas as pd
import pytest

from app.models.account import Account
from app.models.base import AccountType
from app.services.matcher import find_best_match
from app.services.statement_parser import StatementParseError, parse_excel


def _make_excel(rows: list[dict]) -> bytes:
    df = pd.DataFrame(rows)
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    return buffer.getvalue()


def test_parse_excel_with_amount_column():
    file_bytes = _make_excel(
        [
            {"Tarih": "01.03.2024", "Açıklama": "ACME LTD HAVALE", "Tutar": "1.250,50"},
            {"Tarih": "02.03.2024", "Açıklama": "KIRA ODEME", "Tutar": "-500"},
        ]
    )
    lines = parse_excel(file_bytes)
    assert len(lines) == 2
    assert lines[0].amount == 1250.50
    assert lines[1].amount == -500.0


def test_parse_excel_with_debit_credit_columns():
    file_bytes = _make_excel(
        [
            {"Tarih": "01.03.2024", "Açıklama": "TAHSILAT", "Borç": "", "Alacak": "2000"},
            {"Tarih": "02.03.2024", "Açıklama": "ODEME", "Borç": "300", "Alacak": ""},
        ]
    )
    lines = parse_excel(file_bytes)
    assert lines[0].amount == 2000.0
    assert lines[1].amount == -300.0


def test_parse_excel_missing_columns_raises():
    file_bytes = _make_excel([{"Foo": "bar"}])
    with pytest.raises(StatementParseError):
        parse_excel(file_bytes)


def test_matcher_finds_account_by_alias():
    accounts = [
        Account(
            id=1,
            name="ACME Lojistik A.Ş.",
            account_type=AccountType.MUSTERI,
            match_aliases="ACME LTD, ACME TIC",
        ),
        Account(id=2, name="Beta Gıda", account_type=AccountType.TEDARIKCI),
    ]
    candidate = find_best_match("ACME LTD HAVALE EFT", accounts)
    assert candidate is not None
    assert candidate.account_id == 1
    assert candidate.score > 70
