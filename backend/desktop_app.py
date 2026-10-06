"""GÖRKEM masaüstü uygulaması giriş noktası.

Arka planda bir FastAPI (uvicorn) sunucusunu ayrı bir thread'de ayağa
kaldırır ve aynı arayüzü (dashboard, cari, çekler, ekstre, raporlar) bir
PyWebView penceresinde gösterir. Kullanıcı bir tarayıcı açmak zorunda
kalmaz; `app/main.py` içindeki FastAPI uygulaması hiç değişmeden hem bu
masaüstü kabuğunda hem de `uvicorn app.main:app` ile normal bir web
sunucusu olarak çalışabilir.

Geliştirme: `python desktop_app.py`
Paketleme: `pyinstaller build.spec` (bkz. README.md)
"""

from __future__ import annotations

import socket
import threading
import time
import urllib.error
import urllib.request

import uvicorn
import webview

from app.main import app

WINDOW_TITLE = "GÖRKEM — Finans Yönetimi"
STARTUP_TIMEOUT_SECONDS = 15.0


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _run_server(port: int, server_box: list[uvicorn.Server]) -> None:
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    server_box.append(server)
    server.run()


def _wait_until_ready(port: int, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    url = f"http://127.0.0.1:{port}/health"
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=0.5):
                return
        except (urllib.error.URLError, ConnectionError, OSError):
            time.sleep(0.1)
    raise RuntimeError(
        "GÖRKEM sunucusu zaman aşımına uğradı. "
        "Antivirüs/güvenlik duvarı yerel bağlantıyı engelliyor olabilir."
    )


def main() -> None:
    port = _find_free_port()
    server_box: list[uvicorn.Server] = []

    server_thread = threading.Thread(
        target=_run_server, args=(port, server_box), daemon=True
    )
    server_thread.start()
    _wait_until_ready(port, STARTUP_TIMEOUT_SECONDS)

    webview.create_window(
        WINDOW_TITLE,
        f"http://127.0.0.1:{port}/",
        width=1440,
        height=900,
        min_size=(1150, 720),
        background_color="#0f172a",
    )
    webview.start()  # Pencere kapanana kadar bloklar.

    if server_box:
        server_box[0].should_exit = True
    server_thread.join(timeout=5)


if __name__ == "__main__":
    main()
