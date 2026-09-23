"""A call that hangs must end. Three ways of hanging, all against a real socket.

    python scripts/check_deadlines.py

`urlopen(timeout=T)` sets `socket.settimeout(T)`, which bounds ONE `recv` and is rearmed by
every byte that arrives. A provider sending one byte a minute therefore never times out: the
read never returns, `_send` never returns, and the whole generation hangs with nothing in the
process able to stop it. Measured before the fix: with T=1.0 and one byte every 0.4s, the read
was still blocked after five seconds.

The three servers below are the three shapes that has:

  drip-body     the headers arrive, then the body trickles forever
  drip-headers  nothing even gets as far as a status line — this hangs INSIDE urlopen,
                which is why the watchdog is armed at connect() and not on the response
  truncate      a `Content-Length` that lies, and the connection closes early

The third is not a deadline case at all: it is the bug the deadline work uncovered.
`IncompleteRead`, `BadStatusLine` and `json.JSONDecodeError` are not `OSError` and not
`URLError`, so all three used to escape `_send` uncaught — no retry, no named error — and
arrive at the API boundary as a 502 about the wrong thing.

No model, no network, no key: everything here talks to 127.0.0.1.
"""

from __future__ import annotations

import http.server
import json
import threading
import time

from mirag.core.errors import ClientGoneError, DeadlineExceededError, RateLimitedError
from mirag.core.timing import Deadline
from mirag.llm.models import OpenRouterChatModel

BODY = json.dumps({"choices": [{"message": {"content": "hello"}}],
                   "usage": {"prompt_tokens": 1, "completion_tokens": 1}}).encode()


class Handler(http.server.BaseHTTPRequestHandler):
    """One server, three behaviours, chosen by the path."""

    protocol_version = "HTTP/1.1"

    def log_message(self, *_args: object) -> None:
        pass  # the point of this script is its own output

    def do_POST(self) -> None:
        self.rfile.read(int(self.headers.get("Content-Length") or 0))
        mode = self.path.strip("/")
        if mode == "drip-headers":
            # Never a complete status line. `urlopen` itself blocks here.
            try:
                while True:
                    self.wfile.write(b"H")
                    self.wfile.flush()
                    time.sleep(0.4)
            except OSError:
                return
        if mode == "truncate":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(BODY) + 500))  # a promise it will break
            self.end_headers()
            self.wfile.write(BODY[:20])
            self.close_connection = True
            return
        # drip-body: headers arrive, then one byte at a time, forever
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(BODY) + 10_000))
        self.end_headers()
        try:
            while True:
                self.wfile.write(b" ")
                self.wfile.flush()
                time.sleep(0.4)
        except OSError:
            return


def serve() -> tuple[http.server.ThreadingHTTPServer, str]:
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def model(url: str, *, call_timeout_s: float, deadline: Deadline | None = None) -> OpenRouterChatModel:
    built = OpenRouterChatModel("test/model", "key", url=url, timeout_s=30.0,
                                call_timeout_s=call_timeout_s)
    if deadline is not None:
        built.accept_deadline(deadline)
    return built


def main() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))
        if not ok:
            failures.append(name)

    server, base = serve()
    try:
        for mode, expected in (("drip-body", DeadlineExceededError),
                               ("drip-headers", DeadlineExceededError)):
            print(f"\n=== {mode}: the socket never goes quiet ===")
            started = time.monotonic()
            try:
                model(f"{base}/{mode}", call_timeout_s=2.0).complete([{"role": "user", "content": "hi"}], None)
                check("it ended", False, "it returned, which this server cannot do")
            except expected as error:
                took = time.monotonic() - started
                # Three attempts, each capped at half the budget: about 3s of work for a 2s
                # budget. What matters is that it ends at all, and quickly.
                check("it ended", took < 20, f"{took:.1f}s")
                check("the error says it was the clock", "within" in str(error), str(error)[:70])
            except Exception as error:
                check("it ended with the right error", False,
                      f"{type(error).__name__}: {str(error)[:70]}")

        print("\n=== truncate: a body that stops half way ===")
        # Not a deadline case. This is the branch that did not exist: IncompleteRead is not an
        # OSError, so it used to escape `_send` with no retry and no name.
        started = time.monotonic()
        try:
            model(f"{base}/truncate", call_timeout_s=30.0).complete([{"role": "user", "content": "hi"}], None)
            check("it was caught", False, "it returned a usable payload, which it is not")
        except (RateLimitedError, DeadlineExceededError) as error:
            check("it was caught and named", True, f"{type(error).__name__} in "
                                                   f"{time.monotonic() - started:.1f}s")
        except Exception as error:
            check("it was caught and named", False,
                  f"escaped as {type(error).__name__}: {str(error)[:60]}")

        print("\n=== the tab closes mid-call ===")
        cancelled = threading.Event()
        guard = Deadline(300, cancelled)
        threading.Timer(1.0, cancelled.set).start()
        started = time.monotonic()
        try:
            model(f"{base}/drip-body", call_timeout_s=300.0, deadline=guard).complete(
                [{"role": "user", "content": "hi"}], None)
            check("the call was abandoned", False, "it returned")
        except ClientGoneError:
            took = time.monotonic() - started
            check("the call was abandoned", took < 5, f"{took:.1f}s after the tab closed")
        except Exception as error:
            check("the call was abandoned", False, f"{type(error).__name__}: {str(error)[:60]}")

        print("\n=== a healthy call is untouched ===")
        # The same machinery, against a server that answers properly: it must not interfere.
        ok_server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Healthy)
        ok_server.daemon_threads = True
        threading.Thread(target=ok_server.serve_forever, daemon=True).start()
        try:
            answer = model(f"http://127.0.0.1:{ok_server.server_address[1]}/",
                           call_timeout_s=30.0).complete([{"role": "user", "content": "hi"}], None)
            check("it answered", answer.message.get("content") == "hello", str(answer.message)[:60])
        finally:
            ok_server.shutdown()

        print("\n=== no watchdog thread outlived its call ===")
        # The reason ThreadPoolExecutor was rejected: since 3.9 its workers are joined at
        # interpreter exit, so one orphan stops the process exiting at all.
        alive = [t.name for t in threading.enumerate() if t.name == "llm-watchdog"]
        check("every watchdog is gone", not alive, str(alive))
    finally:
        server.shutdown()

    print("\n" + ("ALL PASS" if not failures else f"{len(failures)} FAILED: {failures}"))
    return 1 if failures else 0


class _Healthy(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_args: object) -> None:
        pass

    def do_POST(self) -> None:
        self.rfile.read(int(self.headers.get("Content-Length") or 0))
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(BODY)))
        self.end_headers()
        self.wfile.write(BODY)


if __name__ == "__main__":
    raise SystemExit(main())
