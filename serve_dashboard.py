"""
Tiny dev server that serves the dashboard AND proxies API calls to Docker services.
No CORS issues since everything goes through the same origin.

Usage: python serve_dashboard.py
Then open: http://localhost:9000
"""
import http.server
import json
import os
import urllib.request
import urllib.error

PORT = 9000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIST = os.path.join(BASE_DIR, "frontend", "dist")
WEBSITE_DIST = os.path.join(BASE_DIR, "website", "dist")
DASHBOARD_DIR = FRONTEND_DIST if os.path.isfile(os.path.join(FRONTEND_DIST, "index.html")) else (WEBSITE_DIST if os.path.isfile(os.path.join(WEBSITE_DIST, "index.html")) else BASE_DIR)

# Routes: /api/PORT/path → http://localhost:PORT/path
SERVICE_PORTS = [8000, 8001, 8002, 8003, 8004, 8005, 8080]


class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DASHBOARD_DIR, **kwargs)

    def do_GET(self):
        # Proxy: /api/8080/healthz → http://localhost:8080/healthz
        if self.path.startswith("/api/"):
            self._proxy("GET")
        elif self.path in ["/dashboard", "/test-dashboard", "/test-dashboard.html"]:
            dashboard_file = os.path.join(BASE_DIR, "test-dashboard.html")
            with open(dashboard_file, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == "/" or self.path == "":
            if not os.path.isfile(os.path.join(DASHBOARD_DIR, "index.html")):
                self.path = "/test-dashboard.html"
            else:
                self.path = "/index.html"
            super().do_GET()
        else:
            # Fallback to index.html for SPA client-side routing
            target_path = os.path.join(DASHBOARD_DIR, self.path.lstrip("/"))
            if not os.path.exists(target_path):
                self.path = "/index.html"
            super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/"):
            self._proxy("POST")
        else:
            self.send_error(404)

    def _proxy(self, method):
        # Parse: /api/8080/v1/pipeline/process → port=8080, path=/v1/pipeline/process
        parts = self.path[5:]  # strip "/api/"
        slash_idx = parts.find("/")
        if slash_idx == -1:
            port_str, path = parts, "/"
        else:
            port_str, path = parts[:slash_idx], parts[slash_idx:]

        try:
            port = int(port_str)
        except ValueError:
            self.send_error(400, f"Invalid port: {port_str}")
            return

        url = f"http://localhost:{port}{path}"

        # Read body for POST
        body = None
        if method == "POST":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else None

        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Content-Type", self.headers.get("Content-Type", "application/json"))

        try:
            resp = urllib.request.urlopen(req, timeout=60)
            resp_body = resp.read()
            self.send_response(resp.status)
            self.send_header("Content-Type", resp.headers.get("Content-Type", "application/json"))
            self.send_header("Content-Length", len(resp_body))
            self.end_headers()
            self.wfile.write(resp_body)
        except urllib.error.HTTPError as e:
            resp_body = e.read() if e.fp else b"{}"
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", len(resp_body))
            self.end_headers()
            self.wfile.write(resp_body)
        except Exception as e:
            err = json.dumps({"error": str(e)}).encode()
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", len(err))
            self.end_headers()
            self.wfile.write(err)

    def log_message(self, format, *args):
        msg = format % args
        if "/api/" in msg:
            print(f"  [PROXY] {msg}")
        else:
            print(f"  [STATIC] {msg}")


if __name__ == "__main__":
    print(f"\n  PrimeVector Test Dashboard")
    print(f"  {'=' * 40}")
    print(f"  Open in browser: http://localhost:{PORT}")
    print(f"  Serving from: {DASHBOARD_DIR}")
    print(f"  Proxying API calls to Docker services")
    print(f"  Press Ctrl+C to stop\n")

    server = http.server.HTTPServer(("", PORT), ProxyHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.")
        server.server_close()
