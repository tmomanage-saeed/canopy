"""
Local dashboard server for Aa_Canopy — one server, one port, all dashboards.
Drop-in replacement for `python -m http.server 8080` — serves all files in this
folder exactly the same way, plus:

  1. /api/kpi.xlsx  ->  fetches the latest KPI.xlsx from Dropbox server-side and
                        returns it to the browser (Overview_Dashboard.html needs
                        this because Dropbox's shared-link redirect doesn't send
                        CORS headers on its first hop).

  2. Routes a few dashboards that live in OTHER folders on this machine so they
     are reachable at the plain http://localhost:8080/<name>.html URL the user
     expects, without moving/copying their files. When a request's top-level
     file matches EXTRA_ROOTS, or its Referer header names one of those pages
     (i.e. it's an image/json/xlsx that page is loading via a relative path),
     the file is served from that page's real folder instead of this one.

Run with:  python serve_dashboard.py   (double-click Start_All_Dashboards.bat)
Then open:
  http://localhost:8080/KPI_Report_Template.html
  http://localhost:8080/Overview_Dashboard.html
  http://localhost:8080/Trees_Shrubs_KPI.html
  http://localhost:8080/existing_trees_dashboard.html
  http://localhost:8080/KPI_Dashboard.html

Optional: pass a port number to run on something other than 8080, e.g.
  python serve_dashboard.py 8090
so a second instance (e.g. for one-off testing) never has to fight over --
or kill -- whatever's already listening on 8080.
"""
import http.server
import os
import posixpath
import socketserver
import sys
import urllib.parse
import urllib.request

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
DROPBOX_URL = "https://www.dropbox.com/scl/fi/3v6u2vw3n5lv1kqc0p0vj/KPI-Update_ar_05_26.xlsx?rlkey=5njynv7a8jwov1vtz3rev5lqj&dl=1"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Dashboards that live in other folders but should still open at
# http://localhost:8080/<filename> — keyed by the file's own name.
EXTRA_ROOTS = {
    "existing_trees_dashboard.html": r"C:\Users\saeed\Downloads\EPD_test",
    "KPI_Dashboard.html": r"C:\Users\saeed\Downloads\KPI_Dashboard",
}


class Handler(http.server.SimpleHTTPRequestHandler):
    def _select_directory(self):
        parsed = urllib.parse.urlparse(self.path)
        basename = posixpath.basename(urllib.parse.unquote(parsed.path))
        if basename in EXTRA_ROOTS:
            return EXTRA_ROOTS[basename]
        referer = self.headers.get("Referer", "")
        for fname, folder in EXTRA_ROOTS.items():
            if fname in referer:
                return folder
        return BASE_DIR

    def do_GET(self):
        self.directory = self._select_directory()
        if self.path == "/api/kpi.xlsx":
            self.proxy_kpi_file()
        else:
            super().do_GET()

    def do_HEAD(self):
        self.directory = self._select_directory()
        super().do_HEAD()

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
        print(f"Serving dashboards at http://localhost:{PORT}")
        print(f"  http://localhost:{PORT}/KPI_Report_Template.html")
        print(f"  http://localhost:{PORT}/Overview_Dashboard.html")
        print(f"  http://localhost:{PORT}/Trees_Shrubs_KPI.html")
        print(f"  http://localhost:{PORT}/existing_trees_dashboard.html")
        print(f"  http://localhost:{PORT}/KPI_Dashboard.html")
        print("Press Ctrl+C in this window to stop the server.")
        httpd.serve_forever()
