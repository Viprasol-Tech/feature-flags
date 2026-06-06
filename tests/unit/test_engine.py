"""Correctness tests for the feature flag engine."""

from __future__ import annotations

import pytest

from feature_flags.engine import FlagEngine, UserContext
from feature_flags.flag import Comparator, Flag, TargetingRule
from feature_flags.store import FlagStore

engine = FlagEngine()


def _user(uid: str, **attrs: object) -> UserContext:
    return UserContext(uid, dict(attrs))


def test_off_flag_is_always_false() -> None:
    flag = Flag(key="f", enabled=False, rollout=100)
    for uid in ("a", "b", "c", "d"):
        assert engine.is_enabled(flag, _user(uid)) is False


def test_full_rollout_always_true() -> None:
    flag = Flag(key="f", rollout=100)
    for uid in ("a", "b", "c", "d", "e", "f", "g"):
        assert engine.is_enabled(flag, _user(uid)) is True


def test_zero_rollout_always_false() -> None:
    flag = Flag(key="f", rollout=0, default=False)
    for uid in ("a", "b", "c", "d", "e", "f", "g"):
        assert engine.is_enabled(flag, _user(uid)) is False


def test_rollout_is_deterministic() -> None:
    flag = Flag(key="checkout", rollout=37)
    first = {uid: engine.is_enabled(flag, _user(uid)) for uid in (f"u{i}" for i in range(50))}
    # Re-evaluate with a freshly built flag — must be identical.
    flag2 = Flag(key="checkout", rollout=37)
    second = {uid: engine.is_enabled(flag2, _user(uid)) for uid in first}
    assert first == second


def test_rollout_is_roughly_proportional() -> None:
    flag = Flag(key="exp", rollout=30)
    n = 10_000
    enabled = sum(engine.is_enabled(flag, _user(f"user-{i}")) for i in range(n))
    fraction = enabled / n
    # Deterministic SHA-256 bucketing should land close to the target rate.
    assert 0.27 <= fraction <= 0.33


def test_different_flags_bucket_independently() -> None:
    a = Flag(key="flag-a", rollout=50)
    b = Flag(key="flag-b", rollout=50)
    n = 2_000
    same = sum(
        engine.is_enabled(a, _user(f"u{i}")) == engine.is_enabled(b, _user(f"u{i}"))
        for i in range(n)
    )
    # If they bucketed identically, agreement would be ~100%. Salting by key
    # decorrelates them, so agreement should hover near 50%.
    assert 0.40 <= same / n <= 0.60


def test_targeting_rule_overrides_rollout() -> None:
    # 0% rollout would normally disable everyone, but the rule forces it on.
    flag = Flag(
        key="beta",
        rollout=0,
        rules=[TargetingRule(attribute="plan", values=["enterprise"], serve=True)],
        default=False,
    )
    assert engine.is_enabled(flag, _user("x", plan="enterprise")) is True
    assert engine.is_enabled(flag, _user("y", plan="free")) is False


def test_targeting_rule_can_force_off() -> None:
    # 100% rollout would enable everyone, but a serve=False rule excludes a group.
    flag = Flag(
        key="risky",
        rollout=100,
        rules=[TargetingRule(attribute="country", values=["KP"], serve=False)],
    )
    assert engine.is_enabled(flag, _user("a", country="KP")) is False
    assert engine.is_enabled(flag, _user("b", country="IN")) is True


def test_first_matching_rule_wins() -> None:
    flag = Flag(
        key="ordered",
        rollout=0,
        rules=[
            TargetingRule(attribute="role", values=["admin"], serve=True),
            TargetingRule(attribute="role", values=["admin"], serve=False),
        ],
    )
    assert engine.is_enabled(flag, _user("a", role="admin")) is True


def test_in_comparator_matches_any_value() -> None:
    flag = Flag(
        key="regions",
        rollout=0,
        rules=[
            TargetingRule(
                attribute="country",
                comparator=Comparator.IN,
                values=["IN", "US", "DE"],
                serve=True,
            )
        ],
    )
    assert engine.is_enabled(flag, _user("a", country="US")) is True
    assert engine.is_enabled(flag, _user("b", country="DE")) is True
    assert engine.is_enabled(flag, _user("c", country="FR")) is False


def test_missing_attribute_does_not_match() -> None:
    flag = Flag(
        key="f",
        rollout=0,
        rules=[TargetingRule(attribute="plan", values=["pro"], serve=True)],
        default=False,
    )
    assert engine.is_enabled(flag, _user("a")) is False


def test_default_served_when_outside_rollout() -> None:
    # rollout=0 and no rules -> falls through to default.
    assert engine.is_enabled(Flag(key="f", rollout=0, default=True), _user("a")) is True
    assert engine.is_enabled(Flag(key="f", rollout=0, default=False), _user("a")) is False


def test_rollout_must_be_in_range() -> None:
    with pytest.raises(ValueError):
        Flag(key="f", rollout=101)
    with pytest.raises(ValueError):
        Flag(key="f", rollout=-1)


def test_rule_requires_values() -> None:
    with pytest.raises(ValueError):
        TargetingRule(attribute="plan", values=[])


def test_store_register_update_and_evaluate() -> None:
    store = FlagStore()
    store.register(Flag(key="f", enabled=True, rollout=100))
    assert store.is_enabled("f", _user("a")) is True

    store.update("f", enabled=False)
    assert store.is_enabled("f", _user("a")) is False

    store.update("f", enabled=True, rollout=0, default=False)
    assert store.is_enabled("f", _user("a")) is False

    assert store.keys() == ["f"]


def test_store_rejects_duplicate_and_missing() -> None:
    store = FlagStore()
    store.register(Flag(key="f"))
    with pytest.raises(KeyError):
        store.register(Flag(key="f"))
    with pytest.raises(KeyError):
        store.get("nope")
    with pytest.raises(KeyError):
        store.update("nope", enabled=False)
