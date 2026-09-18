"""Toy authentication: signing and validation of hand-made JWT tokens.

It exists so the indexer has real code to walk, not to be used.
The JWT is built with the stdlib's hmac/hashlib/base64 and IS NOT SECURE: the secret
is hard-coded, and there is no rotation, no 'kid', no 'aud' and no revocation.
Any resemblance to a real service is only in the shape.
"""

import base64
import hashlib
import hmac
import json
import time

# Hard-coded on purpose: this is a test fixture, not a service.
SECRET = b"fake-secret-only-for-the-fixture"
VALIDITY = 3600  # seconds a freshly issued token lasts


def _b64(data: bytes) -> str:
    """base64url without '=': it is what the JWT format asks for."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(text: str) -> bytes:
    """The inverse of _b64: puts back the padding the format strips."""
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def sign_token(payload: dict, secret: bytes = SECRET) -> str:
    """Issues an HS256 JWT with that payload. Only HS256: 'alg' is not negotiated."""
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = _b64(json.dumps(payload).encode())
    signature = hmac.new(secret, f"{header}.{body}".encode(), hashlib.sha256).digest()
    return f"{header}.{body}.{_b64(signature)}"


def verify_jwt(token: str, secret: bytes = SECRET) -> dict:
    """Checks the HMAC signature of a JWT and returns its payload.

    It does not look at the expiry: that is validate_token's job. The only question
    answered here is 'was this signed by who it claims'.
    """
    try:
        header, body, signature = token.split(".")
    except (ValueError, AttributeError):
        raise ValueError("malformed token") from None
    # The token's own 'alg' is deliberately not read: reading it is how 'alg: none' sneaks in.
    expected = hmac.new(secret, f"{header}.{body}".encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(expected, _unb64(signature)):  # constant-time comparison
        raise ValueError("invalid signature")
    return json.loads(_unb64(body))


def validate_token(token: str) -> dict:
    """Validates a JWT token: checks the signature and that it has not expired."""
    payload = verify_jwt(token, SECRET)
    if payload.get("exp", 0) < time.time():
        raise ValueError("expired token")
    return payload


class AuthService:
    """Issues tokens for a user. Keeps the secret so it does not read the global."""

    def __init__(self, secret: bytes = SECRET):
        self.secret = secret

    def issue_token(self, user_id: str, validity: int = VALIDITY) -> str:
        """Issues a signed JWT for that user, valid for `validity` seconds."""
        return sign_token({"sub": user_id, "exp": int(time.time()) + validity}, self.secret)
