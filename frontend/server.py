"""Serve the static ICheck UI and proxy API calls to the local FastAPI backend."""

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


FRONTEND_DIR = Path(__file__).resolve().parent
BACKEND_URL = "http://127.0.0.1:8000"


class ICheckHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def do_POST(self):
        if not self.path.startswith("/api/"):
            self.send_error(404)
            return

        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        if self.path == "/api/nearby-optometrists":
            request = Request(
                "https://overpass-api.de/api/interpreter",
                data=body,
                headers={
                    "Content-Type": self.headers.get("Content-Type", "application/x-www-form-urlencoded"),
                    "User-Agent": "ICheck educational eye-care finder",
                    "Accept": "application/json",
                },
                method="POST",
            )
            try:
                with urlopen(request, timeout=30) as response:
                    payload = response.read()
                    status = response.status
                    content_type = response.headers.get("Content-Type", "application/json")
            except HTTPError as error:
                payload = error.read()
                status = error.code
                content_type = error.headers.get("Content-Type", "application/json")
            except (URLError, TimeoutError) as error:
                payload = b'{"detail":"Nearby provider search is temporarily unavailable."}'
                status = 502
                content_type = "application/json"

            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        request = Request(
            f"{BACKEND_URL}{self.path}",
            data=body,
            headers={
                "Content-Type": self.headers.get("Content-Type", "application/octet-stream"),
                "Accept": self.headers.get("Accept", "application/json"),
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=120) as response:
                payload = response.read()
                status = response.status
                content_type = response.headers.get("Content-Type", "application/json")
        except HTTPError as error:
            payload = error.read()
            status = error.code
            content_type = error.headers.get("Content-Type", "application/json")
        except (URLError, TimeoutError) as error:
            payload = ('{"detail":"Could not connect to the ICheck API at http://127.0.0.1:8000."}').encode()
            status = 502
            content_type = "application/json"

        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


if __name__ == "__main__":
    address = ("127.0.0.1", 5500)
    print(f"ICheck frontend: http://{address[0]}:{address[1]}")
    print(f"API proxy target: {BACKEND_URL}")
    ThreadingHTTPServer(address, ICheckHandler).serve_forever()
