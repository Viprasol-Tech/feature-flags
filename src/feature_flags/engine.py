"""The flag evaluation engine.

:class:`FlagEngine` resolves a flag for a given user context by applying the
standard precedence used by feature-flag platforms:

1. **Off switch** — if the flag is disabled, return ``False`` immediately.
2. **Targeting** — the first matching :class:`~feature_flags.flag.TargetingRule`
   wins and serves its configured value.
3. **Rollout** — if no rule matched, the user is enabled when they fall inside
   the deterministic percentage rollout.
4. **Default** — otherwise the flag's ``default`` value is served.

Part of Feature Flags by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from typing import Any

from feature_flags.flag import Flag


class UserContext:
    """A user plus their attributes, evaluated against flags.

    Args:
        user_id: Stable identifier used for rollout bucketing. The same id always
            lands in the same rollout bucket for a given flag.
        attributes: Arbitrary key/value attributes consulted by targeting rules,
            e.g. ``{"country": "IN", "plan": "pro"}``.
    """

    __slots__ = ("attributes", "user_id")

    def __init__(self, user_id: str, attributes: dict[str, Any] | None = None) -> None:
        self.user_id = user_id
        self.attributes: dict[str, Any] = dict(attributes or {})

    def __repr__(self) -> str:
        return f"UserContext(user_id={self.user_id!r}, attributes={self.attributes!r})"


class FlagEngine:
    """Stateless evaluator that turns a flag + user into a boolean decision."""

    def is_enabled(self, flag: Flag, user: UserContext) -> bool:
        """Return whether ``flag`` is enabled for ``user``.

        Evaluation order: off -> targeting rules -> rollout -> default.
        """
        if not flag.enabled:
            return False

        for rule in flag.rules:
            if rule.matches(user.attributes):
                return rule.serve

        if flag.in_rollout(user.user_id):
            return True

        return flag.default
