#!/usr/bin/env python3
"""Tiny HTTP smoke server used by CI to validate the image is runnable.

Provides:
 - GET /health -> 200
 - GET /ready  -> 200

This avoids requiring the full backend stack (DB, models) in CI.
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/health", "/ready"):
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            payload = {'status': 'ok', 'path': self.path}
            self.wfile.write(json.dumps(payload).encode('utf-8'))
        elif self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4; charset=utf-8')
            self.end_headers()
            # Provide a minimal prometheus text-format metric so CI can query /metrics
            metrics = '# HELP petra_dummy_metric A dummy metric for smoke tests\n# TYPE petra_dummy_metric gauge\npetra_dummy_metric 1\n'
            self.wfile.write(metrics.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()


def run(host='0.0.0.0', port=8000):
    server = HTTPServer((host, port), Handler)
    print(f"Smoke server listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == '__main__':
    run()
