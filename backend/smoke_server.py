from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import threading
import time

# Global variable to track startup
startup_time = time.time()


class SmokeHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type="text/plain"):
        self.send_response(status)
        self.send_header('Content-type', content_type)
        self.end_headers()

    def do_GET(self):
        # Always serve from main thread, no threading issues
        if self.path in ("/health", "/ready"):
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            payload = {'status': 'ok', 'path': self.path, 'timestamp': time.time()}
            self.wfile.write(json.dumps(payload).encode('utf-8'))
        elif self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4; charset=utf-8')
            self.end_headers()
            # Provide a minimal prometheus text-format metric so CI can query /metrics
            metrics = '# HELP petra_dummy_metric A dummy metric for smoke tests\n# TYPE petra_dummy_metric gauge\npetra_dummy_metric 1\n'
            self.wfile.write(metrics.encode('utf-8'))
        else:
            self._set_headers(404)
            self.wfile.write(b"Not Found")



def run_server(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, SmokeHandler)
    print(f'Starting smoke server on port {port}...')
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()