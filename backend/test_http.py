from http.server import HTTPServer, BaseHTTPRequestHandler

class TestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Hello from FitAI test server!')

server = HTTPServer(('0.0.0.0', 8000), TestHandler)
print('Server started on http://localhost:8000')
server.serve_forever()