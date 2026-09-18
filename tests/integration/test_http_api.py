"""The HTTP boundary, through a real server on a free loopback port."""

from __future__ import annotations

import http.client
import json
import threading
from collections.abc import Iterator
from typing import Any

import pytest

from mirag.api.server import MiragHTTPServer, build_server
from mirag.container import Container

pytestmark = pytest.mark.slow  # it starts a real HTTP server per test


@pytest.fixture
def server(container: Container) -> Iterator[MiragHTTPServer]:
    srv = build_server(container, "127.0.0.1", 0)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    yield srv
    srv.shutdown()
    srv.server_close()


def request(server: MiragHTTPServer, method: str, path: str, body: Any = None,
            headers: dict[str, str] | None = None, raw: bytes | None = None) -> tuple[int, dict[str, str], bytes]:
    host, port = server.server_address[:2]
    connection = http.client.HTTPConnection(host, port, timeout=120)
    payload = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    all_headers = {"Content-Type": "application/json", **(headers or {})}
    connection.request(method, path, body=payload, headers=all_headers)
    response = connection.getresponse()
    data = response.read()
    connection.close()
    return response.status, {k.lower(): v for k, v in response.getheaders()}, data


def events(data: bytes) -> list[dict[str, Any]]:
    return [json.loads(block[6:]) for block in data.decode("utf-8").split("\n\n") if block.startswith("data: ")]


def chat(server: MiragHTTPServer, question: str, locale: str = "en", mode: str = "pipeline") -> list[dict[str, Any]]:
    status, headers, data = request(server, "POST", "/api/v1/chat",
                                    {"question": question, "mode": mode, "locale": locale})
    assert status == 200
    assert headers["content-type"].startswith("text/event-stream")
    return events(data)


# ── the allow-list of routes ─────────────────────────────────────────────────

@pytest.mark.parametrize("path", ["/.env", "/.env.example", "/pyproject.toml", "/src/mirag/container.py",
                                  "/var/traces/pipeline.jsonl", "/../README.md", "/index.html.bak",
                                  "/api/v1/artifacts", "/descarga?id=0", "/chat", "/api/blockchain/agent"])
@pytest.mark.parametrize("method", ["GET", "HEAD"])
def test_nothing_outside_the_allow_list_is_served(server: MiragHTTPServer, path: str, method: str) -> None:
    status, _headers, data = request(server, method, path)
    assert status == 404
    if method == "HEAD":
        assert data == b""


def test_the_page_is_served_with_defensive_headers(server: MiragHTTPServer) -> None:
    status, headers, data = request(server, "GET", "/")
    assert status == 200
    assert headers["content-type"].startswith("text/html")
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert b"<html" in data.lower()
    head_status, head_headers, head_data = request(server, "HEAD", "/")
    assert head_status == 200 and head_data == b""
    assert head_headers["content-length"] == str(len(data))


def test_a_known_path_with_the_wrong_method_is_405(server: MiragHTTPServer) -> None:
    status, _, data = request(server, "POST", "/api/v1/health", {})
    assert status == 405
    assert json.loads(data)["error"]["code"] == "method_not_allowed"


def test_health_and_locales(server: MiragHTTPServer) -> None:
    status, _, data = request(server, "GET", "/api/v1/health")
    health = json.loads(data)
    assert status == 200 and health["status"] == "ok" and health["offline"] is True
    assert health["locales"] == ["en", "es"]
    _, _, data = request(server, "GET", "/api/v1/locales", headers={"Accept-Language": "es-AR,es;q=0.9"})
    assert json.loads(data) == {"default": "es", "supported": ["en", "es"]}


def test_ui_strings_per_locale(server: MiragHTTPServer) -> None:
    status, _, data = request(server, "GET", "/api/v1/i18n/es")
    assert status == 200 and json.loads(data)["locale"] == "es"
    status, _, data = request(server, "GET", "/api/v1/i18n/fr")
    assert status == 404 and json.loads(data)["error"]["code"] == "unknown_locale"


def test_demos_are_localised(server: MiragHTTPServer) -> None:
    _, _, data = request(server, "GET", "/api/v1/demos?locale=es")
    payload = json.loads(data)
    assert payload["locale"] == "es" and payload["offline"] is True
    assert payload["demos"][0]["question"].startswith("¿Qué es un índice")


def test_the_blockchain_panel_never_takes_the_server_down(server: MiragHTTPServer) -> None:
    status, _, data = request(server, "GET", "/api/v1/blockchain/agent")
    payload = json.loads(data)
    assert status == 200 and payload["available"] is False and payload["reason"]


# ── downloads ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(("artifact_id", "expected"), [
    ("0" * 24, 410), ("abc", 400), ("..%2F..%2Fetc%2Fpasswd", 404), ("G" * 24, 400)])
def test_download_ids_are_validated_and_never_touch_the_disk(server: MiragHTTPServer, artifact_id: str,
                                                            expected: int) -> None:
    status, _, data = request(server, "GET", f"/api/v1/artifacts/{artifact_id}/download")
    assert status == expected
    assert b"passwd" not in data


def test_head_never_downloads(server: MiragHTTPServer) -> None:
    status, _, data = request(server, "HEAD", f"/api/v1/artifacts/{'0' * 24}/download")
    assert status == 404 and data == b""


# ── chat ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(("raw", "code"), [
    (b"not json", "invalid_json"), (b"[]", "invalid_body"), (b'{"question": ""}', "missing_question"),
    (b'{"question": 3}', "missing_question"), (b'{"question": "x", "mode": 5}', "invalid_mode"),
    (b'{"question": "x", "locale": 7}', "invalid_locale")])
def test_invalid_chat_requests_are_rejected_before_streaming(server: MiragHTTPServer, raw: bytes, code: str) -> None:
    status, headers, data = request(server, "POST", "/api/v1/chat", raw=raw)
    assert status == 400
    assert headers["content-type"].startswith("application/json")
    assert json.loads(data)["error"]["code"] == code


def test_an_empty_body_is_rejected(server: MiragHTTPServer) -> None:
    status, _, _ = request(server, "POST", "/api/v1/chat", raw=b"")
    assert status == 400


@pytest.mark.parametrize("locale", ["en", "es"])
def test_the_shortcut_answers_about_mirag_in_the_requested_language(server: MiragHTTPServer, locale: str) -> None:
    question = {"en": "which model do you use?", "es": "¿qué modelo usás?"}[locale]
    stream = chat(server, question, locale)
    assert [e["type"] for e in stream] == ["phase", "done"]
    assert stream[-1]["mode"] == "state" and stream[-1]["locale"] == locale


@pytest.mark.parametrize("locale", ["en", "es"])
def test_a_question_outside_the_demos_streams_real_retrieval_and_no_invented_answer(
        server: MiragHTTPServer, locale: str) -> None:
    question = {"en": "How do I implement Raft consensus with linearizability guarantees?",
                "es": "¿Cómo implemento consenso Raft con garantías de linealizabilidad?"}[locale]
    stream = chat(server, question, locale)
    lock = stream[0]
    assert lock["type"] == "step" and lock["name"] == "offline_lock" and lock["status"] == "no_model"
    names = [e.get("name") for e in stream if e["type"] == "step"]
    assert "retrieval" in names and "sufficiency" in names
    done = stream[-1]
    assert done["type"] == "done" and done["locale"] == locale
    assert done["cost"] == {"simulated": True, "demo": None, "calls": 0,
                            "text": {"en": "NO MODEL · $0", "es": "SIN MODELO · $0"}[locale]}
    assert done["timeline"] and all(not r["stage"].startswith("bm25:") for r in done["timeline"])
    assert done["evidence"]["observed"] is None


@pytest.mark.slow
def test_a_code_demo_streams_evidence_and_the_deliverable(server: MiragHTTPServer) -> None:
    stream = chat(server, "Create calculator.py with a function calculate(a, b, operation) and its tests", "en")
    done = stream[-1]
    assert done["evidence"]["observed"]["status"] == "passed"
    assert done["evidence"]["verified"]
    assert done["deliverable"]["status"] == "passed"
    assert "calculator.py" in done["deliverable"]["files"]
    assert done["claim_status"] in ("no_claim", "supported")
    assert done["cost"]["simulated"] is True and done["cost"]["demo"] == "code"


@pytest.mark.slow
def test_the_project_demo_offers_a_download_of_exactly_what_was_verified(server: MiragHTTPServer) -> None:
    import hashlib

    stream = chat(server, "Create a REST API of books with full CRUD, ready to download", "en")
    project = stream[-1]["project"]
    assert project["status"] == "VERIFIED" and project["simulated"] is True
    assert project["integrity"]["ok"] is True
    url = project["download_url"]
    assert url.startswith("/api/v1/artifacts/") and url.endswith("/download")
    status, headers, data = request(server, "GET", url)
    assert status == 200 and headers["content-type"] == "application/zip"
    assert hashlib.sha256(data).hexdigest() == project["zip"]["sha256"] == headers["x-mirag-sha256"]
    assert headers["content-disposition"] == 'attachment; filename="books-api.zip"'


def test_an_unknown_mode_is_answered_not_crashed(server: MiragHTTPServer) -> None:
    done = chat(server, "anything technical about indexes", "en", mode="fast")[-1]
    assert "does not exist" in done["answer"]


def test_the_architect_mode_offline_says_the_run_was_cut(server: MiragHTTPServer) -> None:
    stream = chat(server, "design a payments platform", "en", mode="architect")
    assert stream[0] == {"type": "phase", "text": "1 · Understand"}
    assert stream[-1]["type"] == "done"
