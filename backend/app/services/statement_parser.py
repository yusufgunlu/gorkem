"""Banka ekstrelerini (Excel/PDF) okuyup ortak bir satır listesine dönüştürür.

Banka ekstre formatları bankadan bankaya büyük farklılık gösterir. Bu modül,
framework'ten bağımsız, test edilebilir saf fonksiyonlar içerir:

- `parse_excel` / `parse_pdf`: dosyayı okuyup `RawStatementLine` listesi üretir.
- `parse_statement_file`: dosya uzantısına göre doğru parser'ı seçer.

Sütun adları Türkçe banka ekstrelerinde yaygın görülen varyasyonlara göre
(büyük/küçük harf ve Türkçe karakterden bağımsız) eşleştirilir.
"""

from __future__ import annotations

import datetime
import io
import re
import unicodedata
from dataclasses import dataclass

import pandas as pd
import pdfplumber

# Olası sütun başlıkları -> normalize edilmiş alan adı
COLUMN_ALIASES: dict[str, list[str]] = {
    "date": ["tarih", "islem tarihi", "valor", "valor tarihi", "date"],
    "description": [
        "aciklama",
        "aciklamalar",
        "islem aciklamasi",
        "detay",
        "description",
        "hareket",
    ],
    "debit": ["borc", "borc tutari", "cikis", "debit"],
    "credit": ["alacak", "alacak tutari", "giris", "credit"],
    "amount": ["tutar", "islem tutari", "amount"],
    "balance": ["bakiye", "kalan bakiye", "balance"],
}


@dataclass
class RawStatementLine:
    """Ekstre dosyasından okunan, henüz eşleştirilmemiş tek bir satır."""

    transaction_date: datetime.date
    description: str
    amount: float  # pozitif: alacak/tahsilat, negatif: borç/ödeme
    balance_after: float | None = None


class StatementParseError(Exception):
    pass


def _normalize(text: str) -> str:
    text = str(text).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.replace("ı", "i").replace("ğ", "g").replace("ş", "s")
    text = re.sub(r"[^a-z0-9 ]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _build_column_map(columns: list[str]) -> dict[str, str]:
    """DataFrame sütun adlarını normalize edilmiş alan adlarına eşler."""
    normalized = {col: _normalize(col) for col in columns}
    field_map: dict[str, str] = {}
    for field, aliases in COLUMN_ALIASES.items():
        for col, norm in normalized.items():
            if norm in aliases and field not in field_map:
                field_map[field] = col
    return field_map


def _to_float(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return None if pd.isna(value) else float(value)
    text = str(value).strip()
    if not text:
        return None
    text = text.replace(" ", "")
    # Türkçe sayı formatı: 1.234,56  ->  1234.56
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(".", "").replace(",", ".")
    text = text.replace("TL", "").replace("₺", "").strip()
    try:
        return float(text)
    except ValueError:
        return None


def _to_date(value) -> datetime.date | None:
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    text = str(value).strip()
    for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%y"):
        try:
            return datetime.datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    try:
        parsed = pd.to_datetime(text, dayfirst=True, errors="raise")
        return parsed.date()
    except Exception:
        return None


def _rows_to_lines(df: pd.DataFrame) -> list[RawStatementLine]:
    field_map = _build_column_map(list(df.columns))

    if "date" not in field_map or "description" not in field_map:
        raise StatementParseError(
            "Ekstre dosyasında 'Tarih' ve 'Açıklama' sütunları bulunamadı."
        )
    if "amount" not in field_map and not ({"debit", "credit"} <= field_map.keys()):
        raise StatementParseError(
            "Ekstre dosyasında 'Tutar' ya da 'Borç'/'Alacak' sütunları bulunamadı."
        )

    lines: list[RawStatementLine] = []
    for _, row in df.iterrows():
        date_value = _to_date(row.get(field_map["date"]))
        description = str(row.get(field_map["description"], "")).strip()
        if date_value is None or not description or description.lower() == "nan":
            continue

        if "amount" in field_map:
            amount = _to_float(row.get(field_map["amount"])) or 0.0
        else:
            debit = _to_float(row.get(field_map.get("debit"))) or 0.0
            credit = _to_float(row.get(field_map.get("credit"))) or 0.0
            amount = credit - debit

        balance_after = None
        if "balance" in field_map:
            balance_after = _to_float(row.get(field_map["balance"]))

        lines.append(
            RawStatementLine(
                transaction_date=date_value,
                description=description,
                amount=amount,
                balance_after=balance_after,
            )
        )
    return lines


def parse_excel(file_bytes: bytes) -> list[RawStatementLine]:
    """Excel (.xlsx/.xls) banka ekstresini okur."""
    try:
        df = pd.read_excel(io.BytesIO(file_bytes), dtype=str)
    except Exception as exc:  # noqa: BLE001
        raise StatementParseError(f"Excel dosyası okunamadı: {exc}") from exc
    return _rows_to_lines(df)


def parse_pdf(file_bytes: bytes) -> list[RawStatementLine]:
    """PDF banka ekstresini okur.

    Önce her sayfadaki tabloları (pdfplumber) çıkarmayı dener; tablo
    bulunamazsa ham metni satır bazlı regex ile ayrıştırmaya düşer.
    """
    all_rows: list[list[str]] = []
    header: list[str] | None = None

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if not table or len(table) < 2:
                    continue
                if header is None:
                    header = [str(c) if c else "" for c in table[0]]
                    all_rows.extend(table[1:])
                else:
                    first_row_norm = [_normalize(c) if c else "" for c in table[0]]
                    header_norm = [_normalize(c) for c in header]
                    all_rows.extend(table[1:] if first_row_norm == header_norm else table)

    if header and all_rows:
        df = pd.DataFrame(all_rows, columns=header)
        return _rows_to_lines(df)

    return _parse_pdf_as_text(file_bytes)


_TEXT_LINE_RE = re.compile(
    r"(?P<date>\d{2}[./]\d{2}[./]\d{2,4})\s+"
    r"(?P<description>.+?)\s+"
    r"(?P<amount>-?[\d.,]+)\s*$"
)


def _parse_pdf_as_text(file_bytes: bytes) -> list[RawStatementLine]:
    lines: list[RawStatementLine] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for raw_line in text.splitlines():
                match = _TEXT_LINE_RE.match(raw_line.strip())
                if not match:
                    continue
                date_value = _to_date(match.group("date"))
                amount = _to_float(match.group("amount"))
                if date_value is None or amount is None:
                    continue
                lines.append(
                    RawStatementLine(
                        transaction_date=date_value,
                        description=match.group("description").strip(),
                        amount=amount,
                    )
                )
    if not lines:
        raise StatementParseError(
            "PDF içinde tablo veya tanınabilir hareket satırı bulunamadı."
        )
    return lines


def parse_statement_file(filename: str, file_bytes: bytes) -> list[RawStatementLine]:
    """Dosya adının uzantısına göre uygun parser'ı seçip çalıştırır."""
    lower = filename.lower()
    if lower.endswith((".xlsx", ".xls")):
        return parse_excel(file_bytes)
    if lower.endswith(".pdf"):
        return parse_pdf(file_bytes)
    raise StatementParseError(
        "Desteklenmeyen dosya türü. Lütfen .xlsx, .xls veya .pdf yükleyin."
    )
