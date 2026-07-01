"""loop-wizard status — Check loop results from the CLI.

This command replaces the manual "Open STATE.md" step (Step 6 in README).
It parses STATE.md and/or state.json and renders a beautiful terminal view.

Usage:
    loop-wizard status                     # show all loops
    loop-wizard status ci-sweeper          # show specific loop
    loop-wizard status --watch             # auto-refresh every 30s
    loop-wizard status --json              # machine-readable output
"""

import json
import os
import re
import sys
import time
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()


def parse_state_md(content: str) -> dict:
    """Parse all YAML code blocks from STATE.md into a merged dict."""
    merged = {}
    for match in re.finditer(r"```yaml\n([\s\S]*?)\n```", content):
        try:
            block = yaml.safe_load(match.group(1))
            if isinstance(block, dict):
                merged.update(block)
        except yaml.YAMLError:
            continue
    return merged


def load_loop_state(loop_dir: Path) -> dict:
    """Load state from state.json (preferred) or STATE.md (fallback)."""
    state_json = loop_dir / "state.json"
    state_md = loop_dir / "STATE.md"

    data = {}

    # Prefer state.json for richer, machine-readable data
    if state_json.is_file():
        try:
            data = json.loads(state_json.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    # Merge/fallback to STATE.md
    if state_md.is_file():
        try:
            md_data = parse_state_md(state_md.read_text(encoding="utf-8"))
            # STATE.md fills in anything state.json doesn't have
            for k, v in md_data.items():
                if k not in data or data[k] is None:
                    data[k] = v
        except OSError:
            pass

    data["_loop_name"] = loop_dir.name
    return data


def render_status_panel(data: dict) -> Panel:
    """Render a single loop's state as a rich Panel."""
    loop_name = data.get("_loop_name", data.get("loop", "unknown"))
    status = data.get("status", "UNKNOWN")

    # Status color & glyphs
    status_colors = {
        "COMPLETE": "green",
        "BLOCKED": "yellow",
        "FAILED": "red",
        "RUNNING": "cyan",
        "IDLE": "dim",
    }
    status_glyphs = {
        "COMPLETE": "● COMPLETE",
        "BLOCKED": "◆ BLOCKED",
        "FAILED": "▲ FAILED",
        "RUNNING": "⬢ RUNNING",
        "IDLE": "○ IDLE",
    }
    
    status_upper = str(status).upper()
    color = status_colors.get(status_upper, "white")
    glyph = status_glyphs.get(status_upper, f"⚙ {status_upper}")

    # Build content lines
    lines: list[str] = []
    lines.append(f"[bold {color}]Status: {glyph}[/bold {color}]")

    if data.get("last_run"):
        lines.append(f"Last Run:   {data['last_run']}")
    if data.get("run_id"):
        lines.append(f"Run ID:     {data['run_id']}")
    if data.get("triggered_by"):
        lines.append(f"Triggered:  {data['triggered_by']}")

    lines.append("")

    # Test results
    tests_found = data.get("tests_found")
    tests_fixed = data.get("tests_fixed")
    tests_remaining = data.get("tests_remaining")
    if any(v is not None for v in [tests_found, tests_fixed, tests_remaining]):
        lines.append("─── [bold magenta]TEST RESULTS[/bold magenta] ───")
        if tests_found is not None:
            lines.append(f"  ✦ Found     : {tests_found}")
        if tests_fixed is not None:
            fixed_color = "green" if tests_fixed and int(tests_fixed) > 0 else "dim"
            lines.append(f"  ✦ Fixed     : [{fixed_color}]{tests_fixed}[/{fixed_color}]")
        if tests_remaining is not None:
            rem_color = "red" if tests_remaining and int(tests_remaining) > 0 else "green"
            lines.append(f"  ✦ Remaining : [{rem_color}]{tests_remaining}[/{rem_color}]")
        lines.append("")

    # Changes
    files_changed = data.get("files_changed")
    commits = data.get("commits_made", data.get("commits"))
    pr_url = data.get("pr_url")
    branch = data.get("branch")
    if any(v is not None for v in [files_changed, commits, pr_url]):
        lines.append("─── [bold magenta]CHANGES MADE[/bold magenta] ───")
        if files_changed:
            if isinstance(files_changed, list):
                for f in files_changed:
                    lines.append(f"  • {f}")
            else:
                lines.append(f"  Files: {files_changed}")
        if commits is not None:
            lines.append(f"  ✦ Commits   : {commits}")
        if branch:
            lines.append(f"  ✦ Branch    : {branch}")
        if pr_url:
            lines.append(f"  ✦ PR Link   : [link={pr_url}]{pr_url}[/link]")
        lines.append("")

    # Budget
    cost = data.get("cost_usd")
    tokens = data.get("tokens_used")
    iterations = data.get("iterations_used")
    if any(v is not None for v in [cost, tokens, iterations]):
        lines.append("─── [bold magenta]BUDGET UTILISATION[/bold magenta] ───")
        if cost is not None:
            lines.append(f"  ✦ Cost      : ${float(cost):.2f}")
        if tokens is not None:
            lines.append(f"  ✦ Tokens    : {int(tokens):,}")
        if iterations is not None:
            lines.append(f"  ✦ Iterations: {iterations}")
        lines.append("")

    # Human interaction
    waiting = data.get("waiting_for_human", False)
    action_needed = data.get("human_action_needed")
    if waiting or action_needed:
        lines.append("─── [bold yellow]⚠️ HUMAN ACTION REQUIRED[/bold yellow] ───")
        if action_needed:
            lines.append(f"  [bold yellow]• {action_needed}[/bold yellow]")
        lines.append("")

    # Scheduling
    next_run = data.get("next_run")
    triggered_next = data.get("triggered_next")
    if next_run or triggered_next:
        lines.append("─── [bold magenta]SCHEDULING[/bold magenta] ───")
        if next_run:
            lines.append(f"  ✦ Next Run  : {next_run}")
        if triggered_next:
            if isinstance(triggered_next, list):
                lines.append(f"  ✦ Triggers  : {', '.join(str(t) for t in triggered_next)}")
            else:
                lines.append(f"  ✦ Triggers  : {triggered_next}")

    content = "\n".join(lines).strip()

    # Panel border color matches status
    border_color = color if color != "dim" else "white"
    return Panel(
        content,
        title=f"[bold white] Loop Status: {loop_name} [/bold white]",
        title_align="left",
        border_style=border_color,
        box=box.ROUNDED,
        expand=True,
        padding=(1, 2),
    )


def render_all_loops(loops_dir: Path) -> list[Panel]:
    """Render status panels for all loops."""
    panels = []
    loop_dirs = sorted([d for d in loops_dir.iterdir() if d.is_dir()])
    for loop_dir in loop_dirs:
        data = load_loop_state(loop_dir)
        # Skip if no meaningful state data
        if len(data) <= 1:  # only _loop_name
            continue
        panels.append(render_status_panel(data))
    return panels


@click.command()
@click.argument("loop_name", required=False)
@click.option("--dir", "-d", "target_dir", default=".", help="Project directory containing .loops/")
@click.option("--watch", "-w", is_flag=True, help="Auto-refresh every 30 seconds")
@click.option("--json", "as_json", is_flag=True, help="Output machine-readable JSON")
def status_cmd(loop_name, target_dir, watch, as_json):
    """Check loop results from the CLI — no need to open STATE.md manually.

    \b
    Examples:
        loop-wizard status                  # show all loops
        loop-wizard status ci-sweeper       # show specific loop
        loop-wizard status --watch          # auto-refresh every 30s
        loop-wizard status --json           # JSON output for scripting
    """
    target_dir = os.path.abspath(target_dir)
    loops_dir = Path(target_dir) / ".loops"

    if not loops_dir.is_dir():
        console.print(f"[red]No .loops directory found in {target_dir}[/red]")
        console.print("[dim]  Run 'loop-wizard init' to scaffold a loop first.[/dim]")
        raise click.Abort()

    # ── Single loop ─────────────────────────────────────────────────
    if loop_name:
        loop_dir = loops_dir / loop_name
        if not loop_dir.is_dir():
            console.print(f"[red]Loop '{loop_name}' not found in {loops_dir}[/red]")
            available = [d.name for d in loops_dir.iterdir() if d.is_dir()]
            if available:
                console.print(f"[dim]Available loops: {', '.join(available)}[/dim]")
            raise click.Abort()

        data = load_loop_state(loop_dir)

        if as_json:
            # Remove internal keys
            output = {k: v for k, v in data.items() if not k.startswith("_")}
            click.echo(json.dumps(output, indent=2, default=str))
            return

        if watch:
            _watch_loop(loop_dir)
            return

        console.print()
        console.print(render_status_panel(data))
        console.print()
        return

    # ── All loops ───────────────────────────────────────────────────
    loop_dirs = sorted([d for d in loops_dir.iterdir() if d.is_dir()])
    if not loop_dirs:
        console.print("[yellow]No loops found.[/yellow]")
        return

    if as_json:
        all_states = []
        for ld in loop_dirs:
            data = load_loop_state(ld)
            output = {k: v for k, v in data.items() if not k.startswith("_")}
            output["loop"] = ld.name
            all_states.append(output)
        click.echo(json.dumps(all_states, indent=2, default=str))
        return

    if watch:
        _watch_all(loops_dir)
        return

    console.print()
    for ld in loop_dirs:
        data = load_loop_state(ld)
        if len(data) > 1:
            console.print(render_status_panel(data))
        else:
            console.print(
                Panel(
                    "[dim]No run data yet. Run the loop first.[/dim]",
                    title=f"[bold]{ld.name}[/bold]",
                    border_style="dim",
                )
            )
    console.print()


def _watch_loop(loop_dir: Path):
    """Watch a single loop's status, refreshing every 30 seconds."""
    console.print("[dim]Watching for changes — Ctrl+C to stop[/dim]\n")
    try:
        while True:
            console.clear()
            data = load_loop_state(loop_dir)
            console.print(render_status_panel(data))
            console.print(f"\n[dim]Auto-refreshing every 30s — Ctrl+C to stop[/dim]")
            time.sleep(30)
    except KeyboardInterrupt:
        console.print("\n[dim]Stopped watching.[/dim]")


def _watch_all(loops_dir: Path):
    """Watch all loops, refreshing every 30 seconds."""
    console.print("[dim]Watching for changes — Ctrl+C to stop[/dim]\n")
    try:
        while True:
            console.clear()
            panels = render_all_loops(loops_dir)
            if panels:
                for p in panels:
                    console.print(p)
            else:
                console.print("[yellow]No loop data found yet.[/yellow]")
            console.print(f"\n[dim]Auto-refreshing every 30s — Ctrl+C to stop[/dim]")
            time.sleep(30)
    except KeyboardInterrupt:
        console.print("\n[dim]Stopped watching.[/dim]")
