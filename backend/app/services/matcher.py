"""Ekstre satırlarını cari hesaplarla eşleştiren bulanık (fuzzy) eşleştirici.

Eşleştirme açıklama metnine (cari adı veya alias'ları) dayanır; tutar burada
bir filtre olarak kullanılmaz çünkü ekstre tutarları genelde kısmi
ödemeler/tahsilatlar olabilir. İleride IBAN tabanlı tam eşleştirme de bu
modüle eklenebilir.
"""

from __future__ import annotations

from dataclasses import dataclass

from rapidfuzz import fuzz, process

from app.models.account import Account


@dataclass
class MatchCandidate:
    account_id: int
    account_name: str
    score: float  # 0-100


def find_best_match(
    description: str, accounts: list[Account]
) -> MatchCandidate | None:
    """Verilen ekstre açıklaması için en iyi cari hesap eşleşmesini bulur."""
    if not accounts or not description:
        return None

    # account_id -> alias listesi
    choices: dict[str, int] = {}
    for account in accounts:
        for alias in account.alias_list():
            choices[alias] = account.id

    if not choices:
        return None

    result = process.extractOne(
        description, choices.keys(), scorer=fuzz.token_set_ratio
    )
    if result is None:
        return None

    matched_alias, score, _ = result
    account_id = choices[matched_alias]
    account = next(a for a in accounts if a.id == account_id)
    return MatchCandidate(account_id=account.id, account_name=account.name, score=score)


def rank_matches(
    description: str, accounts: list[Account], limit: int = 3
) -> list[MatchCandidate]:
    """En iyi `limit` kadar eşleşme adayını skoruna göre sıralı döner.

    Manuel eşleştirme ekranında kullanıcıya birden fazla seçenek sunmak için
    kullanılır.
    """
    choices: dict[str, int] = {}
    for account in accounts:
        for alias in account.alias_list():
            choices[alias] = account.id

    if not choices:
        return []

    results = process.extract(
        description, choices.keys(), scorer=fuzz.token_set_ratio, limit=limit * 3
    )

    seen_accounts: set[int] = set()
    candidates: list[MatchCandidate] = []
    for alias, score, _ in results:
        account_id = choices[alias]
        if account_id in seen_accounts:
            continue
        seen_accounts.add(account_id)
        account = next(a for a in accounts if a.id == account_id)
        candidates.append(MatchCandidate(account_id=account.id, account_name=account.name, score=score))
        if len(candidates) >= limit:
            break
    return candidates
