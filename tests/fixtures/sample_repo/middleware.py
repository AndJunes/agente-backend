"""Minimal HTTP middleware: the door every request walks through.

Kept apart from auth.py on purpose: that way the indexer has a relationship between
files to discover (this module calls validate_token).
"""

from auth import validate_token


def auth_middleware(request: dict, next) -> dict:
    """Validates the request's JWT token before letting it through to the route."""
    header = request.get("headers", {}).get("Authorization", "")
    if not header.startswith("Bearer "):
        return {"status": 401, "body": "the Authorization header is missing"}
    try:
        request["user"] = validate_token(header[len("Bearer "):])
    except ValueError as exc:
        return {"status": 401, "body": str(exc)}
    return next(request)


def cors_middleware(request: dict, next) -> dict:
    """Adds the CORS headers to the response. Useful noise: it has nothing to do with auth."""
    response = next(request)
    response.setdefault("headers", {})["Access-Control-Allow-Origin"] = "*"
    return response
