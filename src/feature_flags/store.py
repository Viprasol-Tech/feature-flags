"""An in-memory flag store with register/update semantics.

The store is intentionally tiny and pluggable: it is the single source of truth
for flag definitions in a process. A real deployment would back this with a
database or config service, but the in-memory implementation keeps the demo and
tests fully offline while exercising the genuine register/update/evaluate path.

Part of Feature Flags by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from typing import Any

from feature_flags.engine import FlagEngine, UserContext
from feature_flags.flag import Flag


class FlagStore:
    """A mutable collection of :class:`Flag` objects keyed by ``flag.key``."""

    def __init__(self) -> None:
        self._flags: dict[str, Flag] = {}
        self._engine = FlagEngine()

    def register(self, flag: Flag) -> Flag:
        """Add a new flag.

        Raises:
            KeyError: if a flag with the same key already exists.
        """
        if flag.key in self._flags:
            raise KeyError(f"flag {flag.key!r} already registered")
        self._flags[flag.key] = flag
        return flag

    def update(self, key: str, **changes: Any) -> Flag:
        """Replace fields of an existing flag and return the updated copy.

        Args:
            key: The key of the flag to update.
            **changes: Field overrides (e.g. ``rollout=50`` or ``enabled=False``).

        Raises:
            KeyError: if no flag with ``key`` exists.
        """
        existing = self.get(key)
        updated = existing.model_copy(update=changes)
        # Re-validate the merged model so invalid updates are rejected.
        updated = Flag.model_validate(updated.model_dump())
        self._flags[key] = updated
        return updated

    def get(self, key: str) -> Flag:
        """Return the flag registered under ``key``.

        Raises:
            KeyError: if no flag with ``key`` exists.
        """
        if key not in self._flags:
            raise KeyError(f"flag {key!r} is not registered")
        return self._flags[key]

    def keys(self) -> list[str]:
        """Return the registered flag keys in insertion order."""
        return list(self._flags)

    def is_enabled(self, key: str, user: UserContext) -> bool:
        """Evaluate the flag registered under ``key`` for ``user``."""
        return self._engine.is_enabled(self.get(key), user)
