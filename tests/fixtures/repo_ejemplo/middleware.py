"""Middleware HTTP minimo: la puerta por la que pasan las peticiones.

Separado de auth.py a proposito: asi el indexador tiene una relacion entre
archivos que descubrir (este modulo llama a validate_token).
"""

from auth import validate_token


def auth_middleware(request: dict, next) -> dict:
    """Valida el token JWT de la peticion antes de dejar pasar a la ruta."""
    cabecera = request.get("headers", {}).get("Authorization", "")
    if not cabecera.startswith("Bearer "):
        return {"status": 401, "body": "falta el header Authorization"}
    try:
        request["user"] = validate_token(cabecera[len("Bearer "):])
    except ValueError as e:
        return {"status": 401, "body": str(e)}
    return next(request)


def cors_middleware(request: dict, next) -> dict:
    """Añade los headers CORS a la respuesta. Ruido util: no tiene que ver con auth."""
    respuesta = next(request)
    respuesta.setdefault("headers", {})["Access-Control-Allow-Origin"] = "*"
    return respuesta
