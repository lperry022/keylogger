# receiver_http.py
import json, queue
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

incoming_events = queue.Queue()

class EventHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        print(f"[HTTP] {self.client_address[0]} -> {self.path}")

        # allow /event and /event/
        if self.path.rstrip("/") != "/event":
            self._reply(404, b"Not found"); return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except Exception:
            length = 0

        body_bytes = self.rfile.read(length)
        body_txt   = body_bytes.decode(self._charset(), "replace")

        print("[HTTP] headers:", dict(self.headers))
        print("[HTTP] body[:200]:", body_txt[:200])

        try:
            evt = json.loads(body_txt)
            evt["_remote"] = self.client_address[0]
            incoming_events.put(evt)
            self._reply(200, b"OK")
        except Exception as e:
            msg = f"bad json: {e}".encode("utf-8", "replace")
            self._reply(400, msg)

    def _charset(self):
        ct = self.headers.get("Content-Type", "")
        # handle application/json; charset=utf-8
        if "charset=" in ct.lower():
            return ct.split("charset=", 1)[1].strip().strip('"').strip("'")
        return "utf-8"

    def _reply(self, code, body=b""):
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def log_message(self, *args, **kwargs):
        pass  # keep BaseHTTP quiet; we print our own lines

def start_http_server(listen_ip="0.0.0.0", port=5050):
    httpd = ThreadingHTTPServer((listen_ip, port), EventHandler)
    print(f"[HTTP] listening on {listen_ip}:{port}")
    httpd.serve_forever()
