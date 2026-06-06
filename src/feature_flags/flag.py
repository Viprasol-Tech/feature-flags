"""Flag definitions: boolean state, percentage rollouts, and targeting rules.

A :class:`Flag` is the unit of configuration the engine evaluates. It carries:

* an ``enabled`` master switch (off => always ``False``),
* an optional ``rollout`` percentage in ``[0, 100]`` that gradually exposes a
  feature to a deterministic subset of users, and
* an ordered list of :class:`TargetingRule` objects that can force a flag on or
  off for users whose attributes match.

The rollout bucketing is a pure function of ``flag-key + user-id``: the same
user always lands in the same bucket for a given flag, with no server state and
no randomness. This makes rollouts reproducible across processes and machines.

Part of Feature Flags by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import hashlib
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

# Number of buckets a user can fall into. Using 100 maps cleanly to a percentage.
_BUCKETS = 100


class Comparator(str, Enum):
    """How a :class:`TargetingRule` compares a user attribute to its values."""

    EQUALS = "equals"
    """The attribute must equal the single rule value."""

    IN = "in"
    """The attribute must be one of the rule values."""


class TargetingRule(BaseModel):
    """A single attribute-based override.

    When a rule matches, it short-circuits evaluation and forces the flag to the
    rule's ``serve`` value, bypassing the percentage rollout entirely.

    Args:
        attribute: The key looked up in the user context (e.g. ``"country"``).
        comparator: How to compare (:class:`Comparator`).
        values: The values to compare against. ``equals`` uses the first value.
        serve: The boolean result to serve when the rule matches.
    """

    attribute: str
    comparator: Comparator = Comparator.EQUALS
    values: list[Any] = Field(default_factory=list)
    serve: bool = True

    @field_validator("values")
    @classmethod
    def _require_values(cls, v: list[Any]) -> list[Any]:
        if not v:
            raise ValueError("a targeting rule needs at least one value")
        return v

    def matches(self, context: dict[str, Any]) -> bool:
        """Return ``True`` if this rule applies to ``context``.

        A missing attribute never matches.
        """
        if self.attribute not in context:
            return False
        actual = context[self.attribute]
        if self.comparator is Comparator.EQUALS:
            return bool(actual == self.values[0])
        # Comparator.IN
        return actual in self.values


class Flag(BaseModel):
    """A feature flag.

    Args:
        key: Stable identifier used both for lookup and rollout bucketing.
        enabled: Master switch. When ``False`` the flag is always off.
        rollout: Percentage in ``[0, 100]`` of users to enable. ``100`` means
            everyone passes the rollout gate; ``0`` means no one does.
        rules: Ordered targeting rules; the first match wins.
        default: Value served when the flag is enabled, no rule matches, and the
            user falls outside the rollout. Usually ``False``.
    """

    key: str
    enabled: bool = True
    rollout: int = 100
    rules: list[TargetingRule] = Field(default_factory=list)
    default: bool = False

    @field_validator("rollout")
    @classmethod
    def _check_rollout(cls, v: int) -> int:
        if not 0 <= v <= _BUCKETS:
            raise ValueError("rollout must be between 0 and 100 inclusive")
        return v

    def bucket(self, user_id: str) -> int:
        """Return the deterministic bucket ``[0, 100)`` for ``user_id``.

        The bucket is derived from a SHA-256 hash of ``"<key>:<user_id>"`` so it
        is stable across runs, processes, and machines, and well distributed so
        that a rollout of ``p`` percent enables roughly ``p`` percent of users.
        """
        digest = hashlib.sha256(f"{self.key}:{user_id}".encode()).digest()
        # Use 8 bytes for a wide, uniform integer before reducing mod 100.
        value = int.from_bytes(digest[:8], "big")
        return value % _BUCKETS

    def in_rollout(self, user_id: str) -> bool:
        """Return ``True`` if ``user_id`` falls within the rollout percentage."""
        if self.rollout >= _BUCKETS:
            return True
        if self.rollout <= 0:
            return False
        return self.bucket(user_id) < self.rollout
