"""loop-wizard dashboard — Aggregate state across all loops.

Reads state.json from all .loops/*/ directories and renders a summary
table with total cost, commits, and loops waiting for human action.
"""

import json
import os
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()


@click.command()
@click.argument("target_dir", default=".")
def dashboard_cmd(target_dir):
    """Aggregate health overview across all loops.

    Reads state.json files from .loops/*/ directories and renders a
    summary table with status, cost, tokens, commits, and human-wait flags.
    """
    target_dir = os.path.abspath(target_dir)
    loops_dir = Path(target_dir) / ".loops"

    if not loops_dir.is_dir():
        console.print(f"[red]No .loops directory found in {target_dir}[/red]")
        raise click.Abort()

    # Find all state.json files
    state_files = sorted(loops_dir.glob("*/state.json"))

    if not state_files:
        console.print("[yellow]No state.json files found. Run some loops first![/yellow]")
        console.print("[dim]  state.json is auto-generated after each loop run.[/dim]")
        return

    # ── Build the dashboard table ───────────────────────────────────
    table = Table(
        title="[bold white]Loop Dashboard Overview[/bold white]",
        title_justify="left",
        show_header=True,
        header_style="bold magenta",
        box=box.ROUNDED,
        border_style="dim",
    )
    table.add_column("Loop", style="bold")
    table.add_column("Status")
    table.add_column("Last Run")
    table.add_column("Cost ($)", justify="right")
    table.add_column("Tokens", justify="right")
    table.add_column("Commits", justify="right")
    table.add_column("Human Wait?")

    total_cost = 0.0
    total_tokens = 0
    total_commits = 0
    highest_cost_val = -1.0
    highest_cost_loop = "None"
    most_commits_val = -1
    most_commits_loop = "None"
    waiting_loops: list[str] = []

    for state_file in state_files:
        try:
            data = json.loads(state_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            console.print(f"[yellow]Could not read {state_file}: {exc}[/yellow]")
            continue

        loop_name = data.get("loop", state_file.parent.name)
        cost = data.get("cost_usd", 0.0)
        tokens = data.get("tokens_used", 0)
        commits = data.get("commits", 0)
        status = data.get("status", "UNKNOWN")
        run_id = data.get("run_id", "Unknown")
        waiting = data.get("waiting_for_human", False)

        total_cost += cost
        total_tokens += tokens
        total_commits += commits

        if cost > highest_cost_val:
            highest_cost_val = cost
            highest_cost_loop = loop_name
        if commits > most_commits_val:
            most_commits_val = commits
            most_commits_loop = loop_name
        if waiting:
            waiting_loops.append(loop_name)

        # Format status with color
        if status == "COMPLETE":
            status_str = f"[green]● {status}[/green]"
        elif status == "FAILED":
            status_str = f"[red]▲ {status}[/red]"
        elif status == "BLOCKED":
            status_str = f"[yellow]◆ {status}[/yellow]"
        elif status == "RUNNING":
            status_str = f"[cyan]⬢ {status}[/cyan]"
        elif status == "IDLE":
            status_str = f"[dim]○ {status}[/dim]"
        else:
            status_str = f"[white]{status}[/white]"

        # Parse last run date from run_id
        last_run = run_id
        if isinstance(run_id, str) and len(run_id) >= 10:
            last_run = run_id[:10]  # YYYY-MM-DD portion

        human_wait = "[bold yellow]▲ WAIT[/bold yellow]" if waiting else "[dim]—[/dim]"

        table.add_row(
            loop_name,
            status_str,
            last_run,
            f"${cost:.2f}",
            f"{tokens:,}",
            str(commits),
            human_wait,
        )

    # ── Render ──────────────────────────────────────────────────────
    console.print()
    console.print(table)

    # Total Metrics Panel
    metrics_table = Table.grid(padding=(0, 2))
    metrics_table.add_column(style="bold cyan")
    metrics_table.add_column(justify="right")
    metrics_table.add_row("✦ Total Cost    :", f"[green]${total_cost:.2f}[/green]")
    metrics_table.add_row("✦ Total Tokens  :", f"[magenta]{total_tokens:,}[/magenta]")
    metrics_table.add_row("✦ Total Commits :", f"[white]{total_commits}[/white]")

    # Aggregate Insights Panel
    insights_lines = []
    insights_lines.append(
        f"  [cyan]▸ Highest Cost Loop :[/cyan] {highest_cost_loop} "
        f"(${highest_cost_val:.2f})" if highest_cost_val >= 0 else "  [cyan]▸ Highest Cost Loop :[/cyan] None"
    )
    insights_lines.append(
        f"  [cyan]▸ Most Commits Loop :[/cyan] {most_commits_loop} "
        f"({most_commits_val} commits)" if most_commits_val >= 0 else "  [cyan]▸ Most Commits Loop :[/cyan] None"
    )
    if waiting_loops:
        insights_lines.append(f"  [yellow bold]▲ Waiting for Human :[/yellow bold] [yellow]{', '.join(waiting_loops)}[/yellow]")
    else:
        insights_lines.append(f"  [green]✔ Waiting for Human :[/green] [green]None[/green]")

    # Layout using grid/columns
    summary_table = Table.grid(padding=(0, 4))
    summary_table.add_column()
    summary_table.add_column()
    summary_table.add_row(
        Panel(
            metrics_table,
            title="[bold white]Overall Metrics[/bold white]",
            border_style="bright_blue",
            padding=(1, 2)
        ),
        Panel(
            "\n".join(insights_lines),
            title="[bold white]Aggregate Insights[/bold white]",
            border_style="bright_blue",
            padding=(1, 2)
        )
    )

    console.print()
    console.print(summary_table)
    console.print()
