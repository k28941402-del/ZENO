"""
Entry point for the packaged standalone build (see .github/workflows/release.yml).
Starts the same Flask app as `zeno-web`, then opens it in the default browser —
this is what "just download and run" actually launches, no terminal required.
"""

from __future__ import annotations

import threading
import time
import webbrowser

from zeno.webui import create_app

URL = "http://127.0.0.1:8420"


def _open_browser_when_ready() -> None:
    time.sleep(1.2)
    webbrowser.open(URL)


def main() -> None:
    threading.Thread(target=_open_browser_when_ready, daemon=True).start()
    print(f"ZENO is running at {URL} — opening your browser now.")
    print("Close this window to stop ZENO.")
    app = create_app()
    app.run(host="127.0.0.1", port=8420, debug=False)


if __name__ == "__main__":
    main()
