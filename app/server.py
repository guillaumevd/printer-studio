"""Loopback-only HTTP UI; mutation requests require an unguessable session token."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import secrets
from urllib.parse import urlsplit
from .catalog import ROOT, catalog
from .paths import VERSION

def make_server(service, port):
    token = secrets.token_urlsafe(32)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, status, data, content_type="application/json; charset=utf-8"):
            if not isinstance(data, bytes):
                data = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'; connect-src 'self'")
            self.end_headers()
            self.wfile.write(data)

        def valid_host(self):
            return self.headers.get("Host") in {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}

        def do_GET(self):
            if not self.valid_host():
                return self.send(403, {"error": "Host rejected"})
            path = urlsplit(self.path).path
            if path == "/api/state":
                return self.send(200, dict(**service.snapshot(), catalog=catalog(), token=token,
                                          application="printer-studio", version=VERSION))
            if path == "/api/log":
                return self.send(200, service.snapshot().get("job"))
            relative = "index.html" if path == "/" else path.lstrip("/")
            file = (ROOT / "web" / relative).resolve()
            if not file.is_relative_to(ROOT / "web") or not file.is_file():
                return self.send(404, {"error": "Page not found"})
            return self.send(200, file.read_bytes(), (mimetypes.guess_type(file.name)[0] or "application/octet-stream") + "; charset=utf-8")

        def do_POST(self):
            if not self.valid_host() or self.headers.get("X-Studio-Token") != token:
                return self.send(403, {"error": "Invalid session. Reload the page."})
            origin = self.headers.get("Origin")
            if origin and origin not in {f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"}:
                return self.send(403, {"error": "Origin rejected"})
            try:
                length = int(self.headers.get("Content-Length", 0))
                if not 0 <= length <= 4096:
                    raise ValueError("Request too large")
                data = json.loads(self.rfile.read(length) or b"{}")
                if self.path == "/api/scan":
                    return self.send(200, service.scan())
                if self.path == "/api/update":
                    if data.get("confirmed") is not True:
                        raise ValueError("Confirm the firmware change.")
                    return self.send(202, service.start(data.get("serial"), data.get("source"), data.get("target")))
                return self.send(404, {"error": "Action unknowne"})
            except (ValueError, KeyError, TypeError) as exc:
                return self.send(409, {"error": str(exc)})
            except Exception as exc:
                return self.send(500, {"error": str(exc)})
    return ThreadingHTTPServer(("127.0.0.1", port), Handler)
