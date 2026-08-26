#!/usr/bin/env python3
"""Start the bundled web UI and expose it inside a Google Colab notebook."""

from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SERVER = ROOT / "service" / "scripts" / "server.py"


def _port_is_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.25):
            return True
    except OSError:
        return False


def launch(port: int = 8765, *, height: int = 800, window: bool = False):
    """Start the service and display its existing web UI in Colab."""
    try:
        from google.colab import output
    except ImportError as exc:
        raise RuntimeError(
            "This launcher is for Google Colab. Locally, run "
            "`python service/scripts/server.py` instead."
        ) from exc

    process = None
    if not _port_is_open("127.0.0.1", port):
        process = subprocess.Popen(
            [
                sys.executable,
                str(SERVER),
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            cwd=ROOT,
        )

        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f"The web server stopped with code {process.returncode}.")
            if _port_is_open("127.0.0.1", port):
                break
            time.sleep(0.2)
        else:
            process.terminate()
            raise RuntimeError("Timed out while starting the web server.")

    print(f"Watermarks Remover is running on Colab port {port}.")
    if window:
        output.serve_kernel_port_as_window(port)
    else:
        output.serve_kernel_port_as_iframe(port, height=height)
    return process


if __name__ == "__main__":
    raise SystemExit(
        "Run this from a Colab Python cell with: "
        "from colab_launcher import launch; server = launch()"
    )
