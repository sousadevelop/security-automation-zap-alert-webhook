import json
import os
from http.server import BaseHTTPRequestHandler

from parser import parse_zap_report
from notifier import dispatch_alert


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if not self._authorized():
            self._send_json(401, {"status": "unauthorized"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length)
            zap_payload = json.loads(raw_body.decode("utf-8") or "{}")
            alerts = parse_zap_report(zap_payload)
            dispatch_result = dispatch_alert(alerts)

            self._send_json(
                200,
                {
                    "status": "processed",
                    "alert_count": len(alerts),
                    "notifier": dispatch_result,
                },
            )
        except json.JSONDecodeError:
            self._send_json(400, {"status": "invalid_json"})
        except Exception as exc:
            self._send_json(500, {"status": "error", "error": str(exc)})

    def do_GET(self):
        self._send_json(405, {"status": "method_not_allowed"})

    def _authorized(self):
        expected_key = os.environ.get("ZAP_API_KEY")
        if not expected_key:
            return True

        provided_key = self.headers.get("X-ZAP-API-Key")
        authorization = self.headers.get("Authorization", "")
        bearer_key = authorization.removeprefix("Bearer ").strip()

        return provided_key == expected_key or bearer_key == expected_key

    def _send_json(self, status_code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
