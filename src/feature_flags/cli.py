"""Command-line interface for Feature Flags.

``feature-flags demo`` registers a flag with a percentage rollout and a targeting
rule, then evaluates it for a handful of users — fully offline, no services.

Part of Feature Flags by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from feature_flags import __version__
from feature_flags.engine import UserContext
from feature_flags.flag import Comparator, Flag, TargetingRule
from feature_flags.store import FlagStore

app = typer.Typer(add_completion=False, help="Feature Flags — by Viprasol Tech.")
console = Console()


@app.command()
def version() -> None:
    """Print the installed version."""
    console.print(f"feature-flags [bold cyan]{__version__}[/] — by Viprasol Tech")


@app.command()
def demo(rollout: int = typer.Option(40, help="Rollout percentage [0-100]")) -> None:
    """Evaluate a flag with a rollout and a targeting rule for several users."""
    store = FlagStore()
    store.register(
        Flag(
            key="new-checkout",
            enabled=True,
            rollout=rollout,
            rules=[
                TargetingRule(
                    attribute="plan",
                    comparator=Comparator.EQUALS,
                    values=["enterprise"],
                    serve=True,
                ),
            ],
            default=False,
        )
    )

    users = [
        UserContext("alice", {"plan": "free"}),
        UserContext("bob", {"plan": "pro"}),
        UserContext("carol", {"plan": "enterprise"}),
        UserContext("dave", {"plan": "free"}),
        UserContext("erin", {"plan": "pro"}),
        UserContext("frank", {"plan": "free"}),
    ]

    table = Table(title=f"Flag 'new-checkout' @ {rollout}% rollout (enterprise forced on)")
    table.add_column("User", style="cyan")
    table.add_column("Plan")
    table.add_column("Bucket", justify="right")
    table.add_column("Enabled", justify="center")

    flag = store.get("new-checkout")
    enabled_count = 0
    for user in users:
        decision = store.is_enabled("new-checkout", user)
        enabled_count += int(decision)
        mark = "[green]ON[/]" if decision else "[red]off[/]"
        table.add_row(
            user.user_id,
            str(user.attributes["plan"]),
            str(flag.bucket(user.user_id)),
            mark,
        )

    console.print(table)
    console.print(f"Enabled for [bold green]{enabled_count}[/]/{len(users)} users (deterministic).")


if __name__ == "__main__":
    app()
