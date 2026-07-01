"""loop-wizard cost — Estimate token and dollar cost before running a loop.

Reads the LOOP.md budget and cadence, applies model pricing, and shows
estimated cost per run and per month.
"""

import os
import re
from pathlib import Path

import click
import requests
import yaml
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from loop_wizard.config import RAW_REPO_URL, MODELS, CADENCE_MULTIPLIERS

console = Console()


def infer_cadence_label(cadence_str: str) -> str:
    """Map a raw cadence string / cron expression to a human label key."""
    c = cadence_str.strip().lower()

    mapping = [
        (lambda s: s in ("hourly",) or s.startswith("0 * * * *"), "hourly"),
        (
            lambda s: s in ("daily", "nightly")
            or any(s.startswith(f"0 {h} * * *") for h in ("2", "3", "8", "9")),
            "nightly",
        ),
        (lambda s: s == "weekly" or bool(re.match(r"^0 \d+ \* \* [0-7]$", s)), "weekly"),
        (lambda s: "pr" in s, "on-pr"),
        (lambda s: "release" in s, "on-release"),
        (lambda s: "merge" in s, "on-merge"),
        (lambda s: "schema" in s or "migration" in s, "on-schema-change"),
        (lambda s: "file" in s or "contract" in s, "on-file-change"),
        (lambda s: "fail" in s or "repair" in s or "test" in s, "on-test-failure"),
        (lambda s: "commit" in s or "push" in s or s == "event-driven", "on-commit"),
    ]

    for check_fn, label in mapping:
        if check_fn(c):
            return label
    return "nightly"


@click.command()
@click.option("--pattern", "-p", required=True, help="Loop pattern name")
@click.option("--cadence", "-c", help="Frequency override (e.g. nightly, weekly)")
@click.option("--model", "-m", default="claude-sonnet", help="Model name for pricing")
def cost_cmd(pattern, cadence, model):
    """Estimate token and dollar cost before running a loop.

    Reads LOOP.md from your project (.loops/<pattern>/LOOP.md) or falls
    back to the remote catalog.
    """
    # ── Load LOOP.md ────────────────────────────────────────────────
    local_path = Path.cwd() / ".loops" / pattern / "LOOP.md"
    content = ""

    if local_path.is_file():
        content = local_path.read_text(encoding="utf-8")
    else:
        console.print(f"[dim]Local loop config not found. Fetching from remote catalog…[/dim]")
        try:
            resp = requests.get(f"{RAW_REPO_URL}/loops/{pattern}/LOOP.md", timeout=15)
            resp.raise_for_status()
            content = resp.text
        except Exception as exc:
            console.print(
                f"[red]Could not retrieve config for '{pattern}' locally or remotely: {exc}[/red]"
            )
            raise click.Abort()

    # ── Parse YAML block ────────────────────────────────────────────
    max_tokens = 50_000
    max_cost = 2.00
    loop_cadence = cadence or "nightly"

    yaml_match = re.search(r"```yaml\n([\s\S]*?)\n```", content)
    if yaml_match:
        try:
            data = yaml.safe_load(yaml_match.group(1))
            if isinstance(data.get("budget"), dict):
                max_tokens = data["budget"].get("max_tokens", max_tokens)
                max_cost = data["budget"].get("max_cost_usd", max_cost)
            if not cadence and data.get("cadence"):
                loop_cadence = infer_cadence_label(str(data["cadence"]))
        except yaml.YAMLError:
            pass

    # ── Calculate estimates ─────────────────────────────────────────
    model_key = model.lower()
    rates = MODELS.get(model_key, MODELS["claude-sonnet"])

    # Assume 80% input, 20% output token split
    est_per_run = (max_tokens * 0.8 / 1_000_000 * rates["input"]) + (
        max_tokens * 0.2 / 1_000_000 * rates["output"]
    )
    runs_per_month = CADENCE_MULTIPLIERS.get(loop_cadence, 30)
    est_per_month = est_per_run * runs_per_month

    # Cap estimates at budget
    est_per_run = min(est_per_run, max_cost)
    est_per_month = min(est_per_month, max_cost * runs_per_month)

    # ── Render table & gauges ───────────────────────────────────────
    console.print()
    console.print(
        Panel(
            f"[bold white]Cost Breakdown for Loop:[/bold white] [bold cyan]{pattern}[/bold cyan] using [bold magenta]{model}[/bold magenta]",
            border_style="bright_blue",
            padding=(0, 2),
            expand=False
        )
    )
    console.print()

    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED, border_style="dim")
    table.add_column("Resource / Constraint", style="bold")
    table.add_column("Value/Estimate", justify="right")

    table.add_row("Max Tokens per Run (Budget)", f"{max_tokens:,} tokens")
    table.add_row("Max Cost per Run (Budget)", f"${max_cost:.2f}")
    table.add_row("Estimated Cost per Run", f"[cyan]${est_per_run:.2f}[/cyan]")
    table.add_row("Cadence (Trigger Frequency)", f"{loop_cadence} (~{runs_per_month} runs/mo)")
    table.add_row("Estimated Cost per Month", f"[green]${est_per_month:.2f}[/green]")

    console.print(table)

    # Token Allocation Gauge
    input_tokens = int(max_tokens * 0.8)
    output_tokens = int(max_tokens * 0.2)
    in_blocks = 24
    out_blocks = 6
    
    console.print("  [bold white]Token Allocation Estimate (80% Input / 20% Output)[/bold white]")
    console.print(f"    Input  : [cyan]" + "█" * in_blocks + f"[/cyan] {input_tokens:,} tokens")
    console.print(f"    Output : [magenta]" + "█" * out_blocks + f"[/magenta] {output_tokens:,} tokens")
    console.print()

    # Monthly Budget Utilisation Gauge
    budget_per_month = max_cost * runs_per_month
    pct_utilisation = (est_per_month / budget_per_month) * 100 if budget_per_month > 0 else 0.0
    filled_blocks = min(30, int(pct_utilisation / 3.33))
    unfilled_blocks = 30 - filled_blocks
    
    gauge_color = "bright_green"
    if pct_utilisation > 80:
        gauge_color = "bright_red"
    elif pct_utilisation > 50:
        gauge_color = "bright_yellow"

    console.print("  [bold white]Estimated Monthly Budget Utilisation[/bold white]")
    console.print(f"    [{gauge_color}]" + "█" * filled_blocks + f"[/{gauge_color}][dim]" + "░" * unfilled_blocks + f"[/dim] {pct_utilisation:.1f}% (${est_per_month:.2f} / ${budget_per_month:.2f})")
    console.print()

    # Recommendations
    if est_per_month > 100:
        console.print(Panel("[bold red]⚠ Alert: High monthly cost projection![/bold red]\nConsider reducing the loop's cadence or lowering the maximum cost per run budget in LOOP.md.", border_style="red", padding=(1, 2), expand=False))
    elif est_per_month > 50:
        console.print(Panel("[bold yellow]ℹ Note: Moderate monthly cost projection.[/bold yellow]\nKeep an eye on execution history and token usage to ensure budget bounds.", border_style="yellow", padding=(1, 2), expand=False))
    else:
        console.print(Panel("[bold green]✓ Healthy: Monthly cost is within conservative boundaries.[/bold green]", border_style="green", padding=(0, 2), expand=False))
        
    console.print()
