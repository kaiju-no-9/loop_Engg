"""loop-wizard audit — Score your loop's production readiness.

Scans .loops/ directories, checks for required files, parses LOOP.md
YAML configuration, and produces a readiness score out of 100.
"""

import os
import re
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()


def parse_loop_yaml(content: str) -> dict | None:
    """Extract and parse the YAML code block from a LOOP.md file."""
    match = re.search(r"```yaml\n([\s\S]*?)\n```", content)
    if not match:
        return None
    try:
        return yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None


def get_score_bar(score: int) -> str:
    """Generate a cyberpunk style progress bar with block characters."""
    filled = int(score / 10)
    unfilled = 10 - filled
    if score >= 80:
        color = "bright_green"
    elif score >= 50:
        color = "bright_yellow"
    else:
        color = "bright_red"
    return f"[{color}]" + "█" * filled + "░" * unfilled + f"[/{color}] {score}/100"


@click.command()
@click.argument("target_dir", default=".")
@click.option("--suggest", is_flag=True, help="Provide improvement suggestions")
def audit_cmd(target_dir, suggest):
    """Score your loop's readiness for production (0–100).

    Checks for required files, verifier, cadence, budget, approval gates,
    file scope, termination conditions, and recovery strategy.
    """
    target_dir = os.path.abspath(target_dir)
    loops_dir = Path(target_dir) / ".loops"

    if not loops_dir.is_dir():
        console.print(f"[red]✖ No .loops directory found in {target_dir}[/red]")
        raise click.Abort()

    loop_dirs = sorted([d for d in loops_dir.iterdir() if d.is_dir()])
    if not loop_dirs:
        console.print("[yellow]⚠ No loops found to audit.[/yellow]")
        return

    for loop_path in loop_dirs:
        loop_name = loop_path.name
        
        # Draw nice section header for each loop
        console.print()
        console.print(
            Panel(
                f"[bold cyan]🔍 AUDITING LOOP:[/bold cyan] [bold white]{loop_name}[/bold white]",
                border_style="bright_blue",
                padding=(0, 2),
                expand=False
            )
        )

        score = 0
        suggestions: list[str] = []
        
        # Build Table for results
        results_table = Table(
            show_header=True,
            header_style="bold magenta",
            box=box.ROUNDED,
            border_style="dim",
            title=f"[bold]Readiness Checks — {loop_name}[/bold]",
            title_justify="left"
        )
        results_table.add_column("Check / Requirement", style="bold")
        results_table.add_column("Status", justify="center")
        results_table.add_column("Score", justify="right")

        # ── File presence checks ────────────────────────────────────
        checks = [
            ("STATE.md", 10, "State file (STATE.md) present", "Create STATE.md file in loop folder"),
            ("SKILL.md", 10, "Triage skill (SKILL.md) present", "Create SKILL.md triage instructions"),
        ]

        for filename, points, label, suggestion in checks:
            if (loop_path / filename).exists():
                score += points
                results_table.add_row(f"✦ {label}", "[green]PASS[/green]", f"[green]{points} / {points}[/green]")
            else:
                suggestions.append(suggestion)
                results_table.add_row(f"▲ {label}", "[red]FAIL[/red]", f"[red]0 / {points}[/red]")

        # ── LOOP.md checks ──────────────────────────────────────────
        loop_md_path = loop_path / "LOOP.md"
        if not loop_md_path.exists():
            suggestions.append("Missing LOOP.md file")
            results_table.add_row("▲ Configuration file (LOOP.md) present", "[red]FAIL[/red]", "0 / 10")
            console.print(results_table)
            
            # Summary panel
            summary_content = f"Readiness Gauge: {get_score_bar(score)}\n\n[red]❌ NOT READY FOR OPERATION[/red]\nMissing critical loop configuration files or verifier commands."
            console.print(Panel(summary_content, title="[bold white]Audit Scorecard[/bold white]", border_style="red", padding=(1, 2), expand=False))
            continue

        score += 10
        results_table.add_row("✦ Configuration file (LOOP.md) present", "[green]PASS[/green]", "10 / 10")

        content = loop_md_path.read_text(encoding="utf-8")
        data = parse_loop_yaml(content)

        if data is None:
            results_table.add_row("▲ Config YAML syntax block readable", "[red]FAIL[/red]", "0 / 70")
            suggestions.append("Fix YAML syntax in LOOP.md or add a ```yaml block")
            console.print(results_table)
            
            # Summary panel
            summary_content = f"Readiness Gauge: {get_score_bar(score)}\n\n[red]❌ NOT READY FOR OPERATION[/red]\nCould not parse configuration block. Fix syntax inside LOOP.md."
            console.print(Panel(summary_content, title="[bold white]Audit Scorecard[/bold white]", border_style="red", padding=(1, 2), expand=False))
            continue

        results_table.add_row("✦ Config YAML syntax block readable", "[green]PASS[/green]", "—")

        # ── YAML field checks ───────────────────────────────────────
        field_checks = [
            (
                lambda d: isinstance(d.get("verifier"), dict) and d["verifier"].get("command"),
                15,
                "Verifier defined (maker-checker pattern)",
                "Define a verifier command to check loop correctness",
            ),
            (
                lambda d: d.get("cadence") is not None,
                10,
                "Cadence/Trigger schedule defined",
                "Define a loop trigger cadence (cron schedule or push)",
            ),
            (
                lambda d: isinstance(d.get("budget"), dict) and d["budget"].get("max_cost_usd"),
                10,
                "Budget cost cap set",
                "Set a budget cap (max_cost_usd) to prevent runaway costs",
            ),
            (
                lambda d: isinstance(d.get("approval_required_for"), list)
                and len(d["approval_required_for"]) > 0,
                10,
                "Approval gates on dangerous actions active",
                "Add approval_required_for rules (e.g. push_to_main)",
            ),
            (
                lambda d: d.get("file_scope") is not None,
                10,
                "Agent file scope defined",
                "Define file_scope (allow/deny) to restrict agent file access",
            ),
            (
                lambda d: isinstance(d.get("termination"), dict)
                and d["termination"].get("success")
                and d["termination"].get("failure"),
                10,
                "Termination triggers defined",
                "Add comprehensive termination conditions (success + failure)",
            ),
            (
                lambda d: d.get("recovery") is not None,
                5,
                "Recovery failover strategy defined",
                "Define recovery strategy (rollback_last_commit, open_issue, etc.)",
            ),
        ]

        for check_fn, points, label, suggestion in field_checks:
            try:
                if check_fn(data):
                    score += points
                    results_table.add_row(f"✦ {label}", "[green]PASS[/green]", f"[green]{points} / {points}[/green]")
                else:
                    suggestions.append(suggestion)
                    results_table.add_row(f"▲ {label}", "[red]FAIL[/red]", f"[red]0 / {points}[/red]")
            except Exception:
                suggestions.append(suggestion)
                results_table.add_row(f"▲ {label} (Error checking)", "[red]ERR[/red]", f"[red]0 / {points}[/red]")

        # ── Worktree isolation (advisory) ───────────────────────────
        has_worktree = data.get("worktree_isolation") is True or data.get("worktree") is True
        if has_worktree:
            results_table.add_row("✦ Worktree isolation enabled", "[green]PASS[/green]", "Advisory")
        else:
            results_table.add_row("⚠ Worktree isolation enabled", "[yellow]WARN[/yellow]", "Advisory")
            suggestions.append("Enable worktree isolation before moving to L3 of trust ramp")

        # Render Table
        console.print(results_table)

        # ── Score summary ───────────────────────────────────────────
        score_color = "green" if score >= 80 else ("yellow" if score >= 50 else "red")
        
        if score >= 80:
            readiness_text = "[green]✦ READY FOR PRODUCTION OPERATION ✦[/green]\nThis loop is fully configured and meets all safety requirements for unattended runs."
        elif score >= 50:
            readiness_text = "[yellow]⚠️ NEEDS IMPROVEMENT FOR UNATTENDED RUNS[/yellow]\nSome safety settings are missing. Ensure budget and file scopes are set."
        else:
            readiness_text = "[red]❌ NOT READY FOR OPERATION[/red]\nMissing critical loop configuration files or verifier commands."

        summary_content = f"Readiness Gauge: {get_score_bar(score)}\n\n{readiness_text}"
        console.print(
            Panel(
                summary_content,
                title="[bold white]Audit Scorecard[/bold white]",
                border_style=score_color,
                padding=(1, 2),
                expand=False
            )
        )

        if suggest and suggestions:
            console.print("\n  [bold yellow]ℹ Suggestions for Improvement:[/bold yellow]")
            for s in suggestions:
                console.print(f"    [yellow]•[/yellow] [white]{s}[/white]")

    console.print()
