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
        if self.path == '/health':
            self.handle_health()
        elif self.path == '/metrics':
            self.handle_metrics()
        else:
            self._set_headers(404)
            self.wfile.write(b"Not Found")

    def handle_health(self):
        # Simulate startup delay
        time.sleep(0.1)
        
        current_time = time.time()
        time_since_startup = current_time - startup_time
        
        # Consider healthy after 1 second
        if time_since_startup >= 1.0:
            self._set_headers(200, "application/json")
            response = json.dumps({
                "status": "healthy",
                "timestamp": current_time,
                "uptime": time_since_startup
            })
            self.wfile.write(response.encode())
        else:
            self._set_headers(503, "application/json")
            response = json.dumps({
                "status": "unhealthy",
                "timestamp": current_time,
                "reason": "service still starting up"
            })
            self.wfile.write(response.encode())

    def handle_metrics(self):
        self._set_headers(200, "text/plain")
        
        # Write Prometheus-formatted metrics
        metrics = [
            "# HELP service_requests_total Total number of requests to the service",
            "# TYPE service_requests_total counter",
            "service_requests_total{endpoint=\"health\"} 42",
            "service_requests_total{endpoint=\"metrics\"} 17",
            "",
            "# HELP service_uptime_seconds Service uptime in seconds",
            "# TYPE service_uptime_seconds gauge",
            f"service_uptime_seconds {time.time() - startup_time}",
            ""
        ]
        
        self.wfile.write("\n".join(metrics).encode())

def run_server(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, SmokeHandler)
    print(f'Starting smoke server on port {port}...')
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()