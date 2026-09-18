"""Almacen de usuarios en memoria. Es RUIDO a proposito.

Ningun simbolo de aqui habla de tokens ni de firmas: sirve para comprobar que
la busqueda discrimina y no devuelve medio repositorio ante cualquier pregunta.
"""

from dataclasses import dataclass, field


@dataclass
class User:
    """Un usuario: lo minimo para que el repositorio tenga algo que guardar."""
    id: str
    email: str
    nombre: str = ""
    etiquetas: list = field(default_factory=list)


class UserRepository:
    """Repositorio de usuarios sobre un dict. Sin base de datos, sin red."""

    def __init__(self):
        self._filas = {}

    def save(self, user: User) -> User:
        """Guarda o reemplaza un usuario por su id."""
        self._filas[user.id] = user
        return user

    def find_by_email(self, email: str) -> User | None:
        """Devuelve el usuario con ese email, o None. Lineal: es un dict de juguete."""
        for fila in self._filas.values():
            if fila.email == email:
                return fila
        return None

    def delete(self, user_id: str) -> bool:
        """Borra un usuario. Devuelve si existia, para que el caller no adivine."""
        return self._filas.pop(user_id, None) is not None

    def count(self) -> int:
        """Cuantos usuarios hay guardados."""
        return len(self._filas)
