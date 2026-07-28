"""
Local dashboard server for Aa_Canopy.
Drop-in replacement for `python -m http.server 8080` — serves all files in this
folder exactly the same way, but also adds one extra route:

    /api/kpi.xlsx  ->  fetches the latest KPI.xlsx from Dropbox server-side and
                        returns it to the browser.

Overview_Dashboard.html needs this because Dropbox's shared-link redirect does
not send CORS headers on its first hop, so browsers block a direct fetch() to
the dropbox.com URL. Fetching it here (server-side, not from the browser) has
no CORS restriction, so the browser just requests /api/kpi.xlsx from itself.

Run with:  python serve_dashboard.py
Then open: http://localhost:8080/Overview_Dashboard.html
"""
import http.server
import socketserver
import urllib.request

PORT = 8080
DROPBOX_URL = "https://www.dropbox.com/scl/fi/mnic6vthj5h3fqbknjqx5/KPI.xlsx?rlkey=4uargirdbzemm5yg893osibqo&dl=1"


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/kpi.xlsx":
            self.proxy_kpi_file()
        else:
            super().do_GET()

    def proxy_kpi_file(self):
        try:
            req = urllib.request.Request(DROPBOX_URL, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            msg = f"Failed to fetch KPI.xlsx from Dropbox: {e}".encode()
            self.send_response(502)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    with ReusableTCPServer(("", PORT), Handler) as httpd:
        print(f"Serving Aa_Canopy dashboard at http://localhost:{PORT}")
        print(f"Overview dashboard: http://localhost:{PORT}/Overview_Dashboard.html")
        httpd.serve_forever()
