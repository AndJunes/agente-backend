"""Autenticacion de juguete: firma y validacion de tokens JWT hechos a mano.

Existe para que el indexador tenga codigo real que recorrer, no para usarse.
El JWT se arma con hmac/hashlib/base64 de la stdlib y NO ES SEGURO: el secreto
esta quemado en el codigo, no hay rotacion, ni 'kid', ni 'aud', ni revocacion.
Cualquier parecido con un servicio de verdad es solo la forma.
"""

import base64
import hashlib
import hmac
import json
import time

# Quemado a proposito: esto es un fixture de pruebas, no un servicio.
SECRET = b"secreto-de-mentira-solo-para-el-fixture"
VIGENCIA = 3600          # segundos que dura un token recien emitido


def _b64(datos: bytes) -> str:
    """base64url sin '=': es lo que pide el formato JWT."""
    return base64.urlsafe_b64encode(datos).rstrip(b"=").decode()


def _des64(txt: str) -> bytes:
    """El inverso de _b64: repone el relleno que el formato quita."""
    return base64.urlsafe_b64decode(txt + "=" * (-len(txt) % 4))


def firmar(payload: dict, secret: bytes = SECRET) -> str:
    """Emite un JWT HS256 con ese payload. Solo HS256: no negociamos 'alg'."""
    cabecera = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    cuerpo = _b64(json.dumps(payload).encode())
    firma = hmac.new(secret, f"{cabecera}.{cuerpo}".encode(), hashlib.sha256).digest()
    return f"{cabecera}.{cuerpo}.{_b64(firma)}"


def verify_jwt(token: str, secret: bytes = SECRET) -> dict:
    """Comprueba la firma HMAC de un JWT y devuelve su payload.

    No mira la expiracion: eso es cosa de validate_token. Aqui solo se responde
    'esta firma la hizo quien dice'.
    """
    try:
        cabecera, cuerpo, firma = token.split(".")
    except (ValueError, AttributeError):
        raise ValueError("token mal formado")
    # El 'alg' del propio token no se lee a proposito: leerlo es como se cuela 'alg: none'.
    esperada = hmac.new(secret, f"{cabecera}.{cuerpo}".encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(esperada, _des64(firma)):   # comparacion en tiempo constante
        raise ValueError("firma invalida")
    return json.loads(_des64(cuerpo))


def validate_token(token: str) -> dict:
    """Valida un token JWT: comprueba la firma y que no haya caducado."""
    payload = verify_jwt(token, SECRET)
    if payload.get("exp", 0) < time.time():
        raise ValueError("token caducado")
    return payload


class AuthService:
    """Emite tokens para un usuario. Guarda el secreto para no leer el global."""

    def __init__(self, secret: bytes = SECRET):
        self.secret = secret

    def issue_token(self, user_id: str, vigencia: int = VIGENCIA) -> str:
        """Emite un JWT firmado para ese usuario, valido durante `vigencia` segundos."""
        return firmar({"sub": user_id, "exp": int(time.time()) + vigencia}, self.secret)
