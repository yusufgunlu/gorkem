"""PyInstaller yapılandırması: GÖRKEM'i tek dosyalık (.exe) bir masaüstü
uygulaması haline getirir.

Kullanım (hedef işletim sisteminin kendisinde çalıştırılmalıdır; PyInstaller
çapraz derleme yapmaz — Windows .exe için Windows'ta, macOS .app için
macOS'ta derleyin):

    pip install -r requirements-dev.txt
    pyinstaller build.spec

Çıktı: dist/GORKEM(.exe)
"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

project_root = Path.cwd()

hidden_imports = (
    collect_submodules("uvicorn")
    + [
        "pydantic",
        "pydantic_settings",
        # numpy'nin PyInstaller hook'u (numpy 2.x) bu ikisini henüz otomatik
        # eklemiyor; eksik kalırsa pandas import anında patlıyor.
        "numpy._core._exceptions",
        "numpy._core._multiarray_umath",
    ]
)

icon_path = project_root / "assets" / "gorkem.ico"

a = Analysis(
    ["desktop_app.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        ("app/templates", "app/templates"),
        ("app/static", "app/static"),
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="GORKEM",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    # Pencereli (konsolsuz) masaüstü uygulaması. Bir sorunu teşhis etmek
    # için konsol çıktısı görmek isterseniz geçici olarak True yapın.
    console=False,
    icon=str(icon_path) if icon_path.exists() else None,
)
