# GÖRKEM — Finans Yönetim Uygulaması

GÖRKEM; gelir/gider, cari hesap, çek/nakit akışı takibini ve banka ekstrelerinin
otomatik olarak sisteme işlenmesini tek bir panelde birleştiren bir finans
yönetim uygulamasıdır. Bu depo, uygulamanın mimarisini ve temel modüllerinin
kod iskeletini içerir.

## Mimari Genel Bakış

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Tarayıcı (Kullanıcı)                       │
│   Jinja2 + TailwindCSS + htmx + Chart.js  →  Sunucu taraflı render,  │
│   kısmi sayfa güncellemeleri (SPA hissi, ağır JS build'i olmadan)    │
└───────────────────────────────┬───────────────────────────────────────┘
                                 │ HTTP (HTML parçaları + JSON)
┌───────────────────────────────▼───────────────────────────────────────┐
│                         FastAPI Uygulaması                            │
│  ┌───────────────┐  ┌────────────────────┐  ┌───────────────────┐    │
│  │  web/ (Jinja2) │  │   api/v1/ (REST)   │  │  services/         │   │
│  │  Dashboard,    │  │  /accounts         │  │  statement_parser  │   │
│  │  Cari, Çek,    │  │  /transactions     │  │  matcher           │   │
│  │  Ekstre, Rapor │  │  /checks           │  │  cashflow          │   │
│  │  sayfaları     │  │  /statements       │  │                     │   │
│  │                │  │  /reports          │  │                     │   │
│  └───────┬────────┘  └─────────┬──────────┘  └──────────┬──────────┘   │
│          │                     │                         │             │
│          └─────────────────────┼─────────────────────────┘             │
│                                 │                                       │
│                      ┌──────────▼───────────┐                          │
│                      │  models/ (SQLAlchemy) │                          │
│                      │  Account, Transaction,│                          │
│                      │  Check, Statement*    │                          │
│                      └──────────┬───────────┘                          │
└─────────────────────────────────┼───────────────────────────────────────┘
                                   │
                         ┌─────────▼─────────┐
                         │   PostgreSQL /     │
                         │   SQLite (dev)     │
                         └────────────────────┘
```

### Katman sorumlulukları

- **`app/models`** — SQLAlchemy ORM modelleri (veritabanı şeması).
- **`app/schemas`** — Pydantic giriş/çıkış şemaları (API sözleşmesi).
- **`app/api/v1`** — REST endpoint'leri (ince katman; iş mantığını
  `services`'e devreder).
- **`app/services`** — İş mantığı: ekstre okuma (Excel/PDF), cari hesap
  eşleştirme, nakit akışı hesaplamaları. Framework'ten bağımsız, test
  edilebilir fonksiyonlar.
- **`app/web`** — Jinja2 tabanlı HTML sayfaları (dashboard, cari, çek,
  ekstre yükleme, raporlar). htmx ile kısmi güncellemeler.
- **`app/core`** — Ayarlar (`config.py`) ve veritabanı bağlantısı
  (`database.py`).

## Temel Modüller

1. **Gelir / Gider ve Cari Takibi**
   - `models/account.py`, `models/transaction.py`
   - `api/v1/accounts.py`, `api/v1/transactions.py`
   - Vadesi yaklaşan/geciken tahsilat-ödemeleri tek ekrandan listeleme.

2. **Çek Hareketleri & Nakit Akışı**
   - `models/check.py` — alınan/verilen çek, durum (portföy, ciro, tahsil,
     karşılıksız).
   - `services/cashflow.py` — çekler + gelir/gider hareketlerini birleştirip
     günlük/haftalık/aylık nakit akışı projeksiyonu üretir.
   - `api/v1/reports.py` → `/reports/cashflow` — Chart.js için zaman
     serisi verisi döner.

3. **Akıllı Ekstre Aktarımı** (kritik özellik)
   - `services/statement_parser.py` — `pandas` ile Excel (.xlsx/.xls),
     `pdfplumber` ile PDF banka ekstrelerini satır satır okuyup ortak bir
     `StatementLine` veri yapısına normalize eder.
   - `services/matcher.py` — açıklama metnini (IBAN, ünvan, anahtar kelime)
     ve tutarı kullanarak `rapidfuzz` ile bulanık eşleştirme yapar, her satır
     için bir cari hesap adayı + güven skoru üretir.
   - `api/v1/statements.py` — dosya yükleme, satırları önizleme, eşleşmeleri
     onaylama/düzeltme ve sisteme işleme uç noktaları.

4. **Finansal Raporlama**
   - `services/cashflow.py`, `api/v1/reports.py`
   - Özelleştirilebilir tarih aralığı ile gelir-gider tablosu ve dönemsel
     nakit akış raporu.

## Veri Modeli (özet)

- **Account** (Cari Hesap): müşteri/tedarikçi, IBAN, vergi no, bakiye.
- **Transaction** (Gelir/Gider): tutar, tür, vade/ödeme tarihi, durum,
  ilişkili cari hesap.
- **Check** (Çek): alınan/verilen, çek no, banka, vade, durum, ilişkili cari
  hesap.
- **StatementImport / StatementLine**: yüklenen ekstre dosyası ve içindeki
  satırlar; her satırın eşleşme durumu ve onaylanmış cari hesabı.

## Geliştirme Ortamı

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Uygulama varsayılan olarak `http://localhost:8000` üzerinde çalışır:

- `/` — Dashboard
- `/docs` — Otomatik oluşturulan OpenAPI (Swagger) dokümantasyonu
- `/cari` — Cari hesap yönetimi
- `/cekler` — Çek takibi
- `/ekstre` — Ekstre yükleme ve eşleştirme ekranı
- `/raporlar` — Finansal raporlar

### Testler

```bash
cd backend
pytest
```

## Kullanılan Teknolojiler

| Katman        | Teknoloji                              |
|---------------|-----------------------------------------|
| Backend       | Python, FastAPI, SQLAlchemy, Pydantic   |
| Veritabanı    | PostgreSQL (prod), SQLite (dev)         |
| Ekstre Okuma  | pandas, openpyxl, pdfplumber            |
| Eşleştirme    | rapidfuzz (bulanık metin eşleştirme)    |
| Arayüz        | Jinja2, TailwindCSS (CDN), htmx, Chart.js |

## Yol Haritası / Sonraki Adımlar

- [ ] Alembic migration'larını ilk şema için oluşturma
- [ ] Kullanıcı kimlik doğrulama / yetkilendirme (JWT)
- [ ] Ekstre eşleştirme için öğrenen (geçmiş onaylardan beslenen) model
- [ ] Çoklu şirket / çoklu kullanıcı desteği
- [ ] Excel/PDF rapor dışa aktarımı
