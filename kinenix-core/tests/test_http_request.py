"""http.request fails on HTTP errors unless the flow handles the status itself, and sends lists as JSON (#163)."""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from kinenix import exit_codes
from kinenix.engine.interpreter import FlowInterpreter
from kinenix.engine.logger import ExecutionLogger
from kinenix.engine.markdown import markdown_to_flow
from kinenix.engine.validation import validate_flow


class _Handler(BaseHTTPRequestHandler):
    received = []

    def _answer(self):
        length = int(self.headers.get("Content-Length") or 0)
        _Handler.received.append(self.rfile.read(length).decode("utf-8"))
        status = int(self.path.strip("/"))
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"answer": status}).encode("utf-8"))

    do_GET = do_POST = _answer

    def log_message(self, *args):
        pass


@pytest.fixture
def server():
    _Handler.received = []
    httpd = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()
    httpd.server_close()


def _run(url, extra=""):
    flow = markdown_to_flow(f"# Call\n\n## Steps\n\n### 1. Call (`http.request`)\n- **url:** {url}\n"
                            f"- **output_var:** `res`\n{extra}")
    return FlowInterpreter(logger=ExecutionLogger(log_dir=None)).run_flow(flow)


@pytest.mark.parametrize("status", [200, 201, 204])
def test_a_success_response_passes(server, status):
    context = _run(f"{server}/{status}")
    assert not context.has_error
    assert context.variables["res"]["status_code"] == status


@pytest.mark.parametrize("status", [400, 404, 500, 503])
def test_an_error_response_fails_the_step_and_says_what_answered(server, status):
    context = _run(f"{server}/{status}")
    assert context.has_error
    assert exit_codes.for_run(context) == exit_codes.TECHNICAL
    message = context.failure_details.error_message
    assert f"HTTP {status}" in message and "answer" in message


@pytest.mark.parametrize("value", ["false", "no"])
def test_fail_on_error_false_leaves_the_status_to_the_flow(server, value):
    context = _run(f"{server}/500", f"- **fail_on_error:** {value}\n")
    assert not context.has_error
    assert context.variables["res"]["status_code"] == 500
    assert context.variables["res"]["body"] == {"answer": 500}


def test_on_error_continue_handles_an_error_response(server):
    context = _run(f"{server}/500", "- **on_error:** continue\n")
    assert not context.has_error and context.variables["res"] is None
    assert exit_codes.for_run(context) == exit_codes.PARTIAL


def test_a_list_payload_is_sent_as_json(server):
    context = _run(f"{server}/200", "- **method:** POST\n- **payload:** [1, 2, 3]\n")
    assert not context.has_error
    assert json.loads(_Handler.received[0]) == [1, 2, 3]


@pytest.mark.parametrize("payload, body", [('{"a": 1}', '{"a": 1}'), ("plain text", "plain text")])
def test_other_payloads_are_sent_as_before(server, payload, body):
    _run(f"{server}/200", f"- **method:** POST\n- **payload:** {payload}\n")
    assert _Handler.received[0] == body


def test_kinenix_validate_accepts_fail_on_error():
    flow = markdown_to_flow("# Call\n\n## Steps\n\n### 1. Call (`http.request`)\n- **url:** http://x.test\n"
                            "- **fail_on_error:** false\n")
    assert validate_flow(flow) == []
