"""Start the API. Uses PORT env if set; otherwise picks the first free port in 8000–8009."""
import os
import socket

import uvicorn


def _pick_port() -> int:
    if "PORT" in os.environ:
        return int(os.environ["PORT"])
    for port in range(8000, 8010):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise SystemExit("No free port found in range 8000–8009. Close other servers or set PORT.")


if __name__ == "__main__":
    port = _pick_port()
    print(f"Open in browser: http://127.0.0.1:{port}/  (UI and API share this port)")
    uvicorn.run("main:app", host="127.0.0.1", port=port)
