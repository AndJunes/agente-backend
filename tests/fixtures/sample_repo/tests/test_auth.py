"""Checks of the fixture itself. No pytest, like everything here: it runs on its own.

    python tests/test_auth.py

Nothing runs at import time on purpose: this file lives inside Mirag's own test tree and
pytest imports it while collecting. That is also why ``auth`` is imported inside each
check and the checks are not called ``test_*``.
"""

import sys
from pathlib import Path

cases = []


def check(name, fn):
    try:
        fn()
        cases.append((True, name, ""))
    except AssertionError as exc:
        cases.append((False, name, str(exc) or "assert"))
    except Exception as exc:
        cases.append((False, name, f"{type(exc).__name__}: {exc}"))


def fresh_token_is_accepted():
    import auth

    service = auth.AuthService()
    payload = auth.validate_token(service.issue_token("u1"))
    assert payload["sub"] == "u1", payload


def token_signed_with_another_secret_is_rejected():
    import auth

    forged = auth.sign_token({"sub": "u1", "exp": 9999999999}, b"another-secret")
    try:
        auth.validate_token(forged)
    except ValueError as exc:
        assert "signature" in str(exc), exc
        return
    raise AssertionError("accepted a token signed with another secret")


def expired_token_is_rejected():
    import auth

    old = auth.sign_token({"sub": "u1", "exp": 0})
    try:
        auth.validate_token(old)
    except ValueError as exc:
        assert "expired" in str(exc), exc
        return
    raise AssertionError("accepted an expired token")


def garbage_only_raises_value_error():
    """A broken token must raise ValueError, not some IndexError."""
    import auth

    for garbage in ("", "no-dots", "a.b.c", None):
        try:
            auth.validate_token(garbage)
        except ValueError:
            continue
        raise AssertionError(f"accepted garbage: {garbage!r}")


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # to import auth.py
    for name, fn in list(globals().items()):
        if callable(fn) and not name.startswith(("check", "_")) and fn.__module__ == "__main__":
            check(name.replace("_", " "), fn)
    for ok, name, error in cases:
        print(f"  {'ok  ' if ok else 'FAIL'} {name}" + (f"  -> {error}" if error else ""))
    failures = sum(1 for ok, _, _ in cases if not ok)
    print(f"\n{len(cases)} cases - {'ALL OK' if not failures else f'{failures} FAILURES'}")
    sys.exit(1 if failures else 0)
