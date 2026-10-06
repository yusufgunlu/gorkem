"""Hem geliştirme (python -m uvicorn) hem de PyInstaller ile paketlenmiş
(.exe) çalışma biçimlerinde doğru dosya yollarını çözer.

PyInstaller tek dosya (`--onefile`) modunda uygulama her açılışta kendini
`sys._MEIPASS` altındaki geçici bir dizine açar; `app/templates` ve
`app/static` gibi veri dosyaları da `build.spec` içindeki `datas` listesiyle
oraya kopyalanır. Geliştirme modunda ise bu dosyalar doğrudan kaynak
ağacında bulunur.
"""

from __future__ import annotations

import sys
from pathlib import Path


def is_frozen() -> bool:
    """PyInstaller tarafından paketlenmiş bir çalıştırılabilir içinde miyiz?"""
    return bool(getattr(sys, "frozen", False))


def get_app_dir() -> Path:
    """`app` paketinin kök dizinini döner (templates/static için temel yol)."""
    if is_frozen():
        return Path(sys._MEIPASS) / "app"  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent


def get_data_dir() -> Path:
    """Veritabanı ve kullanıcı verileri için kalıcı, yazılabilir dizin.

    Bu dizin, uygulamanın kurulduğu/çalıştırıldığı yerden bağımsızdır;
    Program Files gibi salt-okunur konumlara kurulmuş bir .exe için bile
    güvenlidir.
    """
    if sys.platform == "win32":
        base = Path(_env("APPDATA") or Path.home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(_env("XDG_DATA_HOME") or Path.home() / ".local" / "share")

    data_dir = base / "GORKEM"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def _env(name: str) -> str | None:
    import os

    return os.environ.get(name)
