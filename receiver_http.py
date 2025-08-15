import json, queue
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

incoming_events = queue.Queue()

class EventHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path.rstrip("/") != "/event":
            self.send_response(404); self.end_headers(); return
        try:
            n = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(n).decode("utf-8", "replace")
            evt = json.loads(body)
            evt["_remote"] = self.client_address[0]
            incoming_events.put(evt)
            self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
        except Exception as e:
            self.send_response(400); self.end_headers(); self.wfile.write(str(e).encode())

    def log_message(self, *a, **kw):  # keep quiet
        pass

def start_http_server(ip="0.0.0.0", port=5050):
    ThreadingHTTPServer((ip, port), EventHandler).serve_forever()