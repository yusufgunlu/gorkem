# GÖRKEM — Finans Yönetim Uygulaması (Masaüstü)

GÖRKEM; gelir/gider, cari hesap, çek/nakit akışı takibini ve banka ekstrelerinin
otomatik olarak sisteme işlenmesini tek bir panelde birleştiren bir finans
yönetim uygulamasıdır. Uygulama, kullanıcının bilgisayarında kurulumsuz
çalışan tek dosyalık bir masaüstü programı (`.exe` / `.app`) olarak paketlenir;
tarayıcı açmaya gerek yoktur.

## Mimari Genel Bakış

Mimarinin kalbi hâlâ bir FastAPI uygulamasıdır (web sürümüyle aynı kod);
masaüstü deneyimi, bu sunucuyu arka planda sessizce başlatıp sonucu
**PyWebView**'ın açtığı yerel bir pencerede gösteren ince bir kabuktan gelir.
Böylece Tailwind/Chart.js/htmx ile yazılmış arayüzün tamamı değişmeden kalır.

```
┌───────────────────────────────────────────────────────────────────────┐
│                    GORKEM.exe (PyInstaller --onefile)                  │
│                                                                         │
│   ┌─────────────────────────┐        ┌───────────────────────────┐    │
│   │     desktop_app.py       │        │   PyWebView Penceresi      │    │
│   │  • boş bir yerel port     │ spawn  │   (Windows: WebView2 /     │    │
│   │    bulur                 ├───────▶│    Linux: WebKitGTK /      │    │
│   │  • uvicorn'u arka plan    │        │    macOS: Cocoa WebKit)     │    │
│   │    thread'inde başlatır   │        │   → http://127.0.0.1:PORT/ │    │
│   │  • /health hazır olana    │        │   Tarayıcı açılmaz, şık bir │    │
│   │    kadar bekler           │        │   native pencere açılır.   │    │
│   └────────────┬─────────────┘        └──────────────┬──────────────┘   │
│                │ aynı process, farklı thread            │ HTTP (localhost)│
│   ┌────────────▼─────────────────────────────────────────▼────────────┐ │
│   │                      app/main.py — FastAPI Uygulaması               │ │
│   │  ┌───────────────┐  ┌────────────────────┐  ┌───────────────────┐ │ │
│   │  │ web/ (Jinja2)  │  │   api/v1/ (REST)   │  │   services/        │ │ │
│   │  │ Panel, Cari,   │  │  /accounts         │  │  statement_parser  │ │ │
│   │  │ Çekler, Ekstre,│  │  /transactions     │  │  matcher            │ │ │
│   │  │ Raporlar       │  │  /checks           │  │  cashflow           │ │ │
│   │  │                │  │  /statements       │  │                     │ │ │
│   │  │                │  │  /reports          │  │                     │ │ │
│   │  └───────┬────────┘  └─────────┬──────────┘  └──────────┬──────────┘ │ │
│   │          └─────────────────────┼─────────────────────────┘          │ │
│   │                      ┌──────────▼───────────┐                       │ │
│   │                      │  models/ (SQLAlchemy) │                       │ │
│   │                      └──────────┬───────────┘                       │ │
│   └─────────────────────────────────┼───────────────────────────────────┘ │
└─────────────────────────────────────┼─────────────────────────────────────┘
                                       │
                         ┌─────────────▼─────────────┐
                         │  SQLite (kullanıcı veri     │
                         │  dizini, bkz. core/paths.py)│
                         │  Win: %APPDATA%\GORKEM      │
                         │  macOS: ~/Library/.../GORKEM│
                         │  Linux: ~/.local/share/GORKEM│
                         └────────────────────────────┘
```

### Neden PyWebView (CustomTkinter değil)?

Uygulamanın arayüzü zaten Jinja2 + TailwindCSS + Chart.js ile geliştirildi.
PyWebView, bu arayüzü **hiç yeniden yazmadan** yerel bir pencerede gösterir;
CustomTkinter seçeneği ise tüm ekranların widget tabanlı olarak sıfırdan
yazılmasını gerektirir ve grafikler/tablolar için çok daha fazla elle kod
ister. Bu yüzden `desktop_app.py`, mevcut FastAPI uygulamasını değiştirmeden
yeniden kullanır.

### Katman sorumlulukları

- **`desktop_app.py`** — Masaüstü giriş noktası: boş port bulma, uvicorn'u
  arka plan thread'inde başlatma, `/health` ile hazır olma kontrolü,
  PyWebView penceresi açma/kapatma.
- **`app/core/paths.py`** — Geliştirme ve PyInstaller (`.exe`) modları
  arasındaki yol farklarını çözer (şablon/static kaynakları, kalıcı veri
  dizini).
- **`app/models`** — SQLAlchemy ORM modelleri (veritabanı şeması).
- **`app/schemas`** — Pydantic giriş/çıkış şemaları (API sözleşmesi).
- **`app/api/v1`** — REST endpoint'leri (ince katman; iş mantığını
  `services`'e devreder). Masaüstü modunda da aynen çalışır, `/docs`
  üzerinden incelenebilir.
- **`app/services`** — İş mantığı: ekstre okuma (Excel/PDF), cari hesap
  eşleştirme, nakit akışı hesaplamaları. Framework'ten bağımsız, test
  edilebilir fonksiyonlar.
- **`app/web`** — Jinja2 tabanlı HTML sayfaları (dashboard, cari, çek,
  ekstre yükleme, raporlar). PyWebView penceresinde bunlar render edilir.
- **`app/core`** — Ayarlar (`config.py`), veritabanı bağlantısı
  (`database.py`) ve yol çözümleme (`paths.py`).

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
   - `api/v1/statements.py` / `app/web/routes.py` — dosya yükleme
     (`<input type="file">` PyWebView penceresinde de normal çalışır),
     satırları önizleme, eşleşmeleri onaylama/düzeltme ve sisteme işleme.

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
pip install -r requirements-dev.txt
cp .env.example .env
```

**Masaüstü penceresi olarak çalıştırmak** (hedeflenen kullanım biçimi):

```bash
python desktop_app.py
```

**Sade web sunucusu olarak çalıştırmak** (şablon/stil üzerinde hızlı
yineleme için — tarayıcıda `--reload` ile anında görürsünüz):

```bash
uvicorn app.main:app --reload
```

Her iki modda da aynı uygulama şu rotalara sahiptir:

- `/` — Panel (Dashboard)
- `/docs` — Otomatik oluşturulan OpenAPI (Swagger) dokümantasyonu
- `/cari` — Cari hesap yönetimi
- `/cekler` — Çek takibi
- `/ekstre` — Ekstre yükleme ve eşleştirme ekranı
- `/raporlar` — Finansal raporlar

Veritabanı dosyası varsayılan olarak kullanıcının veri dizinine yazılır
(`core/paths.get_data_dir()`): Windows'ta `%APPDATA%\GORKEM\gorkem.db`,
macOS'ta `~/Library/Application Support/GORKEM/gorkem.db`, Linux'ta
`~/.local/share/GORKEM/gorkem.db`. `.env` içindeki `DATABASE_URL` ile
(örn. sunucu dağıtımında PostgreSQL) geçersiz kılınabilir.

### Testler

```bash
cd backend
pytest
```

## Tek Dosyalık `.exe` / Uygulama Paketi Oluşturma

> **Önemli:** PyInstaller çapraz derleme yapmaz. Windows `.exe` üretmek için
> Windows'ta, macOS `.app` için macOS'ta, Linux için Linux'ta derleyin.

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate   # Windows
# source .venv/bin/activate                      # macOS/Linux
pip install -r requirements-dev.txt
pyinstaller build.spec
```

Çıktı: `dist/GORKEM.exe` (Windows) veya `dist/GORKEM` (macOS/Linux) — tek
dosya, kurulum gerektirmez; çift tıklanınca arka planda sunucu ayağa kalkar
ve GÖRKEM penceresi açılır.

- **İkon eklemek isterseniz** `assets/gorkem.ico` (Windows için `.ico`)
  dosyasını ekleyin; `build.spec` otomatik olarak kullanır.
- **Windows** için WebView2 Runtime gereklidir; Windows 10/11'de genelde
  önceden kurulu gelir, yoksa Microsoft'un resmî dağıtıcısından kurulabilir.
- **Linux**'ta derlemeden önce sistemde WebKitGTK/GTK geliştirme paketleri
  kurulu olmalıdır (örn. Debian/Ubuntu: `python3-gi`, `gir1.2-webkit2-4.1`).
- **macOS**'ta ek bir bağımlılık gerekmez (Cocoa WebKit kullanılır); ilk
  çalıştırmada Gatekeeper uyarısı için uygulamanın imzalanması/notarize
  edilmesi önerilir.
- Derleme sırasında antivirüs yazılımları PyInstaller'ın tek-dosya
  açılış adımını (geçici klasöre çıkarma) bazen yanlışlıkla
  işaretleyebilir; gerekirse `dist/` klasörünü istisnaya ekleyin.

## Kullanılan Teknolojiler

| Katman          | Teknoloji                                  |
|-----------------|----------------------------------------------|
| Backend         | Python, FastAPI, SQLAlchemy, Pydantic        |
| Masaüstü Kabuğu | PyWebView (yerel pencere), PyInstaller (.exe)|
| Veritabanı      | SQLite (masaüstü, kullanıcı veri dizini), PostgreSQL (opsiyonel sunucu dağıtımı) |
| Ekstre Okuma    | pandas, openpyxl, pdfplumber                 |
| Eşleştirme      | rapidfuzz (bulanık metin eşleştirme)         |
| Arayüz          | Jinja2, TailwindCSS (CDN), htmx, Chart.js     |

## Yol Haritası / Sonraki Adımlar

- [ ] `assets/gorkem.ico` / `.icns` uygulama ikonlarının eklenmesi
- [ ] Windows/macOS için kod imzalama (code signing) ve otomatik güncelleme
- [ ] Alembic migration'larını ilk şema için oluşturma
- [ ] Kullanıcı kimlik doğrulama / yetkilendirme (çok kullanıcılı/sunucu modu için)
- [ ] Ekstre eşleştirme için öğrenen (geçmiş onaylardan beslenen) model
- [ ] Excel/PDF rapor dışa aktarımı
