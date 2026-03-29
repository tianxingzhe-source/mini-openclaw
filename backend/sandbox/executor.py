"""沙箱内 Python 代码执行服务 — 通过 HTTP 接收代码并在持久命名空间中执行"""

import sys
import io
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

namespace: dict = {}


def execute_code(code: str) -> dict:
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout = captured_out = io.StringIO()
    sys.stderr = captured_err = io.StringIO()
    try:
        exec(code, namespace)
        output = captured_out.getvalue()
        errors = captured_err.getvalue()
        result = output
        if errors:
            result += f"\n[STDERR]: {errors}"
        return {"ok": True, "output": result.strip() or "(代码执行完毕，无输出)"}
    except Exception as e:
        return {"ok": False, "output": f"执行出错: {type(e).__name__}: {str(e)}"}
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr


class ExecutorHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        request = json.loads(body.decode("utf-8"))

        result = execute_code(request.get("code", ""))

        payload = json.dumps(result, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        self.send_response(200)
        body = b'{"status":"ok"}'
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass


def main():
    port = 9999
    server = HTTPServer(("0.0.0.0", port), ExecutorHandler)
    print(f"[sandbox] Python executor ready on port {port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
