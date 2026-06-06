"""Feature Flags — a tiny, deterministic feature flag engine by Viprasol Tech."""

from __future__ import annotations

from feature_flags.engine import FlagEngine
from feature_flags.flag import Comparator, Flag, TargetingRule
from feature_flags.store import FlagStore

__version__ = "0.1.0"
__author__ = "Viprasol Tech Private Limited"
__all__ = [
    "Comparator",
    "Flag",
    "FlagEngine",
    "FlagStore",
    "TargetingRule",
    "__version__",
]
