"""In-memory user store. It is NOISE on purpose.

No symbol here talks about tokens or signatures: it is there to check that the search
discriminates and does not return half the repository for any question.
"""

from dataclasses import dataclass, field


@dataclass
class User:
    """A user: the minimum for the repository to have something to keep."""

    id: str
    email: str
    name: str = ""
    tags: list = field(default_factory=list)


class UserRepository:
    """User repository over a dict. No database, no network."""

    def __init__(self):
        self._rows = {}

    def save(self, user: User) -> User:
        """Saves or replaces a user by its id."""
        self._rows[user.id] = user
        return user

    def find_by_email(self, email: str) -> User | None:
        """Returns the user with that email, or None. Linear: it is a toy dict."""
        for row in self._rows.values():
            if row.email == email:
                return row
        return None

    def delete(self, user_id: str) -> bool:
        """Deletes a user. Returns whether it existed, so the caller does not guess."""
        return self._rows.pop(user_id, None) is not None

    def count(self) -> int:
        """How many users are kept."""
        return len(self._rows)
