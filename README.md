<p align="center">
  <img src="docs/assets/logo.png" width="120" alt="Viprasol Tech logo">
</p>

<h1 align="center">Feature Flags</h1>

<p align="center">
  <strong>A tiny, deterministic feature flag engine — boolean flags, percentage rollouts, and targeting rules — in Python.</strong><br>
  Register a flag, evaluate it for a user, and ship features to exactly who you want — no service, no network.
</p>

<p align="center">
  <em>Built and maintained by <a href="https://viprasol.com">Viprasol Tech</a> — Fintech Experts. Full-Stack Builders.</em>
</p>

<p align="center">
  <a href="https://github.com/Viprasol-Tech/feature-flags/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/Viprasol-Tech/feature-flags/ci.yml?style=flat-square&logo=githubactions&logoColor=white&label=CI" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/Viprasol-Tech/feature-flags?style=flat-square&color=blue" alt="License: MIT"></a>
  <img src="https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
  <a href="https://t.me/viprasol_help"><img src="https://img.shields.io/badge/Telegram-support-26A5E4?style=flat-square&logo=telegram&logoColor=white" alt="Telegram"></a>
  <a href="https://github.com/Viprasol-Tech/feature-flags/stargazers"><img src="https://img.shields.io/github/stars/Viprasol-Tech/feature-flags?style=flat-square&logo=github" alt="Stars"></a>
</p>

---

## ✨ Features

- 🎚️ **Boolean flags** — a master on/off switch; disabled flags are always off.
- 📈 **Percentage rollouts** — expose a feature to *p%* of users via a deterministic
  hash of `flag-key + user-id` (0–100). The same user always gets the same answer.
- 🎯 **Targeting rules** — force a flag on or off for users by attribute
  (`equals` / `in`), evaluated before the rollout.
- 🧮 **Reproducible bucketing** — SHA-256 based, stateless, and well-distributed,
  so a 30% rollout enables ≈30% of users — and the same set every run.
- 🗄️ **In-memory store** — `register` / `update` / `is_enabled` with validation.
- 🖥️ **CLI** — `feature-flags demo --rollout 40` evaluates a flag for several users.
- ⚙️ **Modern tooling** — ruff, mypy (strict), pytest, GitHub Actions CI.

## 🚀 Quickstart

```bash
git clone https://github.com/Viprasol-Tech/feature-flags.git
cd feature-flags
python -m pip install -e ".[dev]"

# Evaluate a flag with a 40% rollout for a set of demo users:
feature-flags demo --rollout 40
```

## 🧩 In-code usage

```python
from feature_flags import Comparator, Flag, FlagEngine, TargetingRule
from feature_flags.engine import UserContext

flag = Flag(
    key="new-checkout",
    enabled=True,
    rollout=25,  # 25% of users
    rules=[
        # ...but every enterprise customer always gets it:
        TargetingRule(attribute="plan", comparator=Comparator.EQUALS,
                      values=["enterprise"], serve=True),
    ],
    default=False,
)

engine = FlagEngine()
engine.is_enabled(flag, UserContext("carol", {"plan": "enterprise"}))  # True (rule)
engine.is_enabled(flag, UserContext("dave", {"plan": "free"}))         # rollout-dependent
```

## 🏗️ Architecture

```mermaid
flowchart LR
    USER[User context] --> ENGINE[FlagEngine.is_enabled]
    STORE[FlagStore] --> ENGINE
    ENGINE --> OFF{enabled?}
    OFF -- no --> FALSE[false]
    OFF -- yes --> RULES{targeting rule matches?}
    RULES -- yes --> SERVE[serve rule value]
    RULES -- no --> ROLL{in rollout %?}
    ROLL -- yes --> TRUE[true]
    ROLL -- no --> DEF[default]
```

## 🗺️ Roadmap

- [x] Boolean flags, percentage rollouts, and targeting rules
- [x] Deterministic SHA-256 bucketing + in-memory store
- [ ] Numeric/regex comparators and rule groups
- [ ] Multivariate flags (string/JSON variants, not just booleans)
- [ ] Pluggable persistent stores (file, Redis, SQL adapters)
- [ ] Evaluation event stream for analytics and A/B testing

## 🤝 Contributing

PRs welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) and our [Code of Conduct](CODE_OF_CONDUCT.md).

## Contact — Viprasol Tech Private Limited

- Website: [viprasol.com](https://viprasol.com)
- Email: [support@viprasol.com](mailto:support@viprasol.com)
- Telegram: [t.me/viprasol_help](https://t.me/viprasol_help) | WhatsApp: +91 96336 52112
- GitHub: [@Viprasol-Tech](https://github.com/Viprasol-Tech) | [LinkedIn](https://www.linkedin.com/in/viprasol/) | X [@viprasol](https://twitter.com/viprasol)

## License

[MIT](LICENSE) (c) 2025 Viprasol Tech Private Limited
