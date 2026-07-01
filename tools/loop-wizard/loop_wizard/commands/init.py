"""loop-wizard init — Scaffold a loop into your project.

Implements the full 5-question interactive wizard from wizard.md:
  1. Test command (verifier.command)
  2. Test directory (file_scope)
  3. Budget (max_cost_usd)
  4. Cadence (cron expression)
  5. Merge strategy (PR vs direct push)
"""

import os
import re
import shutil
import tempfile
from pathlib import Path

import click
import requests
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, FloatPrompt
from rich.table import Table
from rich.text import Text

from loop_wizard.config import (
    RAW_REPO_URL,
    CADENCE_PRESETS,
    AGENT_TOOLS,
    AGENT_ENV_VARS,
    STACK_SIGNATURES,
    DEFAULTS,
)

console = Console()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fetch_registry():
    """Fetch the loop registry from the remote repo."""
    url = f"{RAW_REPO_URL}/patterns/registry.yaml"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        registry = yaml.safe_load(resp.text)
        if registry and isinstance(registry.get("loops"), list):
            return registry["loops"]
    except Exception as exc:
        console.print(f"[red]Failed to fetch loop registry: {exc}[/red]")
    return []


def fetch_file(pattern: str, filename: str) -> str:
    """Fetch a single file from the remote repo for a given pattern."""
    url = f"{RAW_REPO_URL}/loops/{pattern}/{filename}"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.text


def detect_stack(target_dir: str):
    """Auto-detect the project stack by looking for known files."""
    for signature_file, stack_name, test_cmd, test_dir in STACK_SIGNATURES:
        if (Path(target_dir) / signature_file).exists():
            return stack_name, test_cmd, test_dir
    return None, DEFAULTS["test_command"], DEFAULTS["test_dir"]


def command_in_path(cmd: str) -> bool:
    """Check if the first token of a command is in PATH."""
    first_token = cmd.split()[0] if cmd.strip() else ""
    return shutil.which(first_token) is not None


def suggest_test_dirs(target_dir: str) -> list[str]:
    """Return existing test-like directories in the project."""
    candidates = ["test/", "tests/", "__tests__/", "spec/", "e2e/", "src/test/"]
    found = []
    for d in candidates:
        if (Path(target_dir) / d).is_dir():
            found.append(d)
    return found


def validate_cron(expr: str) -> bool:
    """Basic validation of a 5-field cron expression."""
    parts = expr.strip().split()
    return len(parts) == 5


def monthly_cost_projection(cost_per_run: float, cadence_value: str) -> float:
    """Estimate monthly cost based on cadence."""
    cron_to_runs = {
        "0 2 * * *": 30,   # nightly
        "0 * * * *": 720,  # hourly
        "__trigger__": 300, # ~10 pushes/day
        "__manual__": 4,    # ~once a week
    }
    runs = cron_to_runs.get(cadence_value, 30)
    return cost_per_run * runs


def build_loop_md(pattern: str, answers: dict, template: str) -> str:
    """Compile LOOP.md from template by replacing placeholders."""
    result = template
    # Replace {{placeholder}} patterns
    replacements = {
        "test_command": answers.get("test_command", DEFAULTS["test_command"]),
        "test_dir": answers.get("test_dir", DEFAULTS["test_dir"]),
        "budget": str(answers.get("budget", DEFAULTS["budget"])),
        "cadence": answers.get("cadence", DEFAULTS["cadence"]),
        "merge_strategy": answers.get("merge_strategy", DEFAULTS["merge_strategy"]),
    }
    for key, value in replacements.items():
        result = result.replace(f"{{{{{key}}}}}", str(value))

    # If the template doesn't have placeholders, try to patch the YAML block directly
    if "{{" not in template:
        result = _patch_loop_md_yaml(result, answers)

    return result


def _patch_loop_md_yaml(content: str, answers: dict) -> str:
    """Patch specific fields inside the YAML code block in LOOP.md."""
    yaml_match = re.search(r"```yaml\n([\s\S]*?)\n```", content)
    if not yaml_match:
        return content

    yaml_text = yaml_match.group(1)
    try:
        data = yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        return content

    # Patch fields from wizard answers
    if "test_command" in answers and isinstance(data.get("verifier"), dict):
        data["verifier"]["command"] = answers["test_command"]

    if "test_dir" in answers:
        if isinstance(data.get("file_scope"), dict):
            data["file_scope"]["allow"] = [f"{answers['test_dir'].rstrip('/')}/**"]
        # Also patch tools.file_edit.scope if present
        if isinstance(data.get("tools"), list):
            for i, t in enumerate(data["tools"]):
                if isinstance(t, dict) and "file_edit" in t:
                    t["file_edit"]["scope"] = answers["test_dir"]

    if "budget" in answers and isinstance(data.get("budget"), dict):
        data["budget"]["max_cost_usd"] = answers["budget"]

    if "cadence" in answers:
        data["cadence"] = answers["cadence"]

    if "merge_strategy" in answers:
        data["merge_strategy"] = answers["merge_strategy"]

    # Reconstruct — dump YAML back into the code block
    new_yaml = yaml.dump(data, default_flow_style=False, sort_keys=False).strip()
    # Preserve comments at the top of the YAML block
    comment_lines = [l for l in yaml_text.split("\n") if l.strip().startswith("#")]
    if comment_lines:
        new_yaml = "\n".join(comment_lines) + "\n" + new_yaml

    return content[: yaml_match.start(1)] + new_yaml + content[yaml_match.end(1) :]


def build_workflow_yml(pattern: str, cadence: str, agent_tool: str) -> str:
    """Generate a GitHub Actions workflow YAML."""
    # Determine trigger block
    if cadence == "__trigger__":
        trigger_block = "  push:\n    branches: [main]"
    elif cadence == "__manual__":
        trigger_block = "  workflow_dispatch:"
    else:
        trigger_block = f"  schedule:\n    - cron: '{cadence}'\n  workflow_dispatch:"

    # Determine env vars
    env_vars = AGENT_ENV_VARS.get(agent_tool, AGENT_ENV_VARS["claude-code"])
    env_lines = "\n".join(
        f"          {k}: {v}" for k, v in env_vars.items()
    )

    return f"""# Generated by loop-wizard v0.1
# Runs the {pattern} loop.

name: {pattern}

on:
{trigger_block}

permissions:
  contents: write
  pull-requests: write

jobs:
  loop:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Run loop
        run: {agent_tool} /loop {pattern}
        env:
{env_lines}

      - name: Upload STATE.md as artifact
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: loop-state
          path: .loops/{pattern}/STATE.md
"""


def build_state_md(pattern: str) -> str:
    """Generate an initial STATE.md template."""
    return f"""# STATE — {pattern}

<!-- This file is auto-managed by the loop runtime. Do not edit manually. -->
<!-- The Verifier agent updates this file after every loop run. -->

## Current Run

```yaml
last_run:                    # ISO 8601 timestamp of the most recent run
status:                      # COMPLETE | BLOCKED | FAILED | RUNNING | IDLE
run_id:                      # Unique run identifier (date-based)
triggered_by:                # cron | manual | event | chain
```

## Test Results

```yaml
tests_found:                 # Total number of failing tests detected at start
tests_fixed:                 # Number of tests this run successfully fixed
tests_remaining:             # Number of tests still failing after this run
```

## Changes Made

```yaml
files_changed:               # List of files modified in this run
commits_made:                # Number of atomic commits created
branch:                      # Branch name
pr_url:                      # URL of the opened PR (if merge_strategy: pr)
```

## Budget

```yaml
cost_usd:                    # Actual dollar cost of this run
tokens_used:                 # Total tokens consumed
iterations_used:             # Number of fix-verify cycles completed
```

## Human Interaction

```yaml
waiting_for_human: false     # true if the loop needs human input to continue
human_action_needed:         # Description of what the human should do
```

## Scheduling

```yaml
next_run:                    # ISO 8601 timestamp of the next scheduled run
triggered_next:              # Loops triggered by this run's completion
```

## Run History

```yaml
run_log: .loops/{pattern}/loop-run-log.md
```

## Machine-Readable Sidecar

<!-- state.json is auto-generated alongside this file for use by loop-dashboard -->
"""


# ---------------------------------------------------------------------------
# Wizard questions
# ---------------------------------------------------------------------------

def print_question_header(num: int, total: int, title: str, subtitle: str = None):
    """Print a beautiful styled header for a wizard question."""
    box_content = f"[bold white]{title}[/bold white]"
    if subtitle:
        box_content += f"\n[dim]{subtitle}[/dim]"
    
    console.print()
    console.print(
        Panel(
            box_content,
            title=f"[bold magenta]⚡ QUESTION {num} OF {total} ⚡[/bold magenta]",
            title_align="left",
            border_style="magenta",
            padding=(1, 2),
            expand=False,
        )
    )


def ask_test_command(detected_cmd: str, target_dir: str) -> str:
    """Question 1 — What command runs your tests?"""
    default = detected_cmd or DEFAULTS["test_command"]
    print_question_header(
        1, 5,
        "What command runs your tests?",
        "This command must exit 0 for the loop to consider itself done."
    )

    cmd = Prompt.ask(
        "  [cyan]▸ Enter test command[/cyan]",
        default=default,
    )

    if not cmd.strip():
        console.print("[red]  ✖ Test command cannot be blank.[/red]")
        return ask_test_command(detected_cmd, target_dir)

    if not command_in_path(cmd):
        console.print(f"  [yellow]⚠ \"{cmd.split()[0]}\" not found in PATH — is this correct?[/yellow]")
        if not Confirm.ask("  Continue anyway?", default=True):
            return ask_test_command(detected_cmd, target_dir)

    console.print(f"  [green]✔ Verifier set to:[/green] {cmd}")
    return cmd


def ask_test_dir(detected_dir: str, target_dir: str) -> str:
    """Question 2 — Where are your test files?"""
    default = detected_dir or DEFAULTS["test_dir"]
    print_question_header(
        2, 5,
        "Where are your test files?",
        "The agent will only read/write files inside this path."
    )

    test_dir = Prompt.ask(
        "  [cyan]▸ Enter test directory[/cyan]",
        default=default,
    )

    if not test_dir.strip():
        test_dir = default

    # Check if the directory exists
    full_path = Path(target_dir) / test_dir
    if not full_path.exists():
        suggestions = suggest_test_dirs(target_dir)
        if suggestions:
            console.print(
                f"  [yellow]⚠ {test_dir} not found. "
                f"Did you mean {' or '.join(suggestions)}?[/yellow]"
            )
        else:
            console.print(f"  [yellow]⚠ {test_dir} not found in project.[/yellow]")
        if not Confirm.ask("  Continue with this path anyway?", default=True):
            return ask_test_dir(detected_dir, target_dir)

    console.print(f"  [green]✔ File scope set to:[/green] {test_dir}")
    return test_dir


def ask_budget(cadence_value: str = None) -> float:
    """Question 3 — What is your cost limit per run?"""
    print_question_header(
        3, 5,
        "What is your cost limit per run? (USD)",
        "When the limit is hit, the loop stops and waits for a human."
    )

    budget = FloatPrompt.ask(
        "  [cyan]▸ Enter cost limit ($)[/cyan]",
        default=DEFAULTS["budget"],
    )

    if budget < 0.01:
        console.print("  [red]✖ Cost limit must be at least $0.01.[/red]")
        return ask_budget(cadence_value)

    if budget > 10.0:
        console.print(f"  [yellow]⚠ That's ${budget:.2f}/run — are you sure?[/yellow]")
        if not Confirm.ask("  Continue?", default=False):
            return ask_budget(cadence_value)

    # Show monthly projection if cadence is known
    if cadence_value:
        monthly = monthly_cost_projection(budget, cadence_value)
        if monthly > 100:
            console.print(
                f"  [yellow]⚠ At this cadence, this loop could cost up to "
                f"${monthly:.0f}/month.[/yellow]"
            )

    console.print(f"  [green]✔ Budget cap set to:[/green] ${budget:.2f} per run")
    return budget


def ask_cadence() -> str:
    """Question 4 — When should this loop run?"""
    print_question_header(
        4, 5,
        "When should this loop run?",
        "Select a frequency preset or override with a custom cron expression later."
    )

    for i, preset in enumerate(CADENCE_PRESETS, 1):
        indicator = "◉" if i == 1 else "○"
        color = "bright_cyan" if i == 1 else "white"
        rec = " [italic green](recommended)[/italic green]" if i == 1 else ""
        console.print(
            f"  [bold cyan]{i}.[/bold cyan] [bold]{indicator}[/bold] [{color}]{preset['label']}[/{color}]"
            f"  [dim]— {preset['description']}[/dim]{rec}"
        )

    choice = Prompt.ask(
        "\n  [cyan]▸ Select option (1-4)[/cyan]",
        choices=[str(i) for i in range(1, len(CADENCE_PRESETS) + 1)],
        default="1",
    )

    selected = CADENCE_PRESETS[int(choice) - 1]
    cadence_value = selected["value"]

    # Power user override
    custom = Prompt.ask(
        "  [dim]▸ Custom cron override? (Leave blank to keep selection)[/dim]",
        default="",
    )
    if custom.strip():
        if validate_cron(custom.strip()):
            cadence_value = custom.strip()
        else:
            console.print("  [red]✖ Invalid cron expression. Using selected preset.[/red]")

    label = selected["label"]
    if cadence_value != selected["value"]:
        label = cadence_value
    console.print(f"  [green]✔ Cadence set to:[/green] {label} ({cadence_value})")
    return cadence_value


def ask_merge_strategy() -> str:
    """Question 5 — Merge strategy."""
    print_question_header(
        5, 5,
        "When the loop finishes, what merge strategy should be used?",
        "Choose how the verified fixes should be integrated back into your main branch."
    )

    console.print("  [bold cyan]1.[/bold cyan] [bold]◉ Open a PR for me to review[/bold]     [dim]— Recommended (you merge when ready)[/dim]")
    console.print("  [bold cyan]2.[/bold cyan] [bold]○ Commit and push directly[/bold]      [dim]— Fully autonomous (higher trust required)[/dim]")

    choice = Prompt.ask("\n  [cyan]▸ Select option (1-2)[/cyan]", choices=["1", "2"], default="1")

    if choice == "2":
        console.print(
            "  [yellow]⚠ Direct push means commits land without review.\n"
            "    Make sure you have approval_required_for: push_to_main set.[/yellow]"
        )
        if not Confirm.ask("  Continue with direct push?", default=False):
            return ask_merge_strategy()
        console.print("  [green]✔ Merge strategy:[/green] push")
        return "push"

    console.print("  [green]✔ Merge strategy:[/green] PR")
    return "pr"


# ---------------------------------------------------------------------------
# Atomic file writer
# ---------------------------------------------------------------------------

def atomic_write_files(files: dict[str, str]):
    """Write all files atomically — all succeed or none are written.

    Args:
        files: mapping of absolute file path -> content
    """
    # Phase 1: write to temp files
    tmp_dir = tempfile.mkdtemp(prefix="loop-wizard-")
    tmp_map: dict[str, str] = {}  # final_path -> temp_path
    try:
        for final_path, content in files.items():
            tmp_path = os.path.join(tmp_dir, os.path.basename(final_path))
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(content)
            tmp_map[final_path] = tmp_path

        # Phase 2: move temp files to final paths
        for final_path, tmp_path in tmp_map.items():
            os.makedirs(os.path.dirname(final_path), exist_ok=True)
            shutil.move(tmp_path, final_path)

    except Exception as exc:
        # Clean up any partially moved files
        console.print(f"[red]✖ Write failed: {exc}[/red]")
        console.print("[red]  No files were written. Fix the error and re-run.[/red]")
        raise click.Abort()
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Main command
# ---------------------------------------------------------------------------

@click.command()
@click.argument("target_dir", default=".")
@click.option("--pattern", "-p", help="Name of the loop pattern to scaffold")
@click.option("--tool", "-t", "agent_tool", help="Agent tool (e.g. claude-code)")
@click.option("--yes", "-y", "non_interactive", is_flag=True, help="Use all defaults, no prompts")
@click.option("--set", "overrides", multiple=True, help="Override a field: --set key=value")
@click.option("--reconfigure", is_flag=True, help="Reconfigure an existing loop")
def init_cmd(target_dir, pattern, agent_tool, non_interactive, overrides, reconfigure):
    """Scaffold a loop into your project with an interactive wizard.

    Asks 5 questions, writes LOOP.md, SKILL.md, STATE.md, and a GitHub Actions
    workflow — all without you opening a single config file.
    """
    target_dir = os.path.abspath(target_dir)

    # Parse overrides
    override_map = {}
    for ov in overrides:
        if "=" in ov:
            k, v = ov.split("=", 1)
            override_map[k.strip()] = v.strip()

    # ── Banner ──────────────────────────────────────────────────────
    banner_text = Text()
    banner_text.append(" █░░ █▀█ █▀█ █▀█   █░░░█ █ ▀█ ▄▀█ █▀█ █▀▄\n", style="bold magenta")
    banner_text.append(" █▄▄ █▄█ █▄█ █▀▀   ▀▄▀▄▀ █ █▄ █▀█ █▀▄ █▄▀\n", style="bold cyan")
    banner_text.append("\n  ⚡ LOOP ENGINEERING WIZARD v0.1 ⚡", style="bold white")
    
    console.print()
    console.print(
        Panel(
            banner_text,
            border_style="bright_blue",
            padding=(1, 4),
            expand=False,
        )
    )

    # ── Fetch registry ──────────────────────────────────────────────
    console.print("[blue]Fetching loop registry…[/blue]")
    loops = fetch_registry()
    if not loops:
        console.print("[red]No patterns found in loop registry.[/red]")
        raise click.Abort()

    pattern_names = [l["name"] for l in loops]

    # ── Select pattern ──────────────────────────────────────────────
    if not pattern:
        if non_interactive:
            console.print("[red]--pattern is required in non-interactive mode.[/red]")
            raise click.Abort()

        console.print("\n[bold]Available loop patterns:[/bold]\n")
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=4)
        table.add_column("Pattern")
        table.add_column("Description")
        table.add_column("Domain", style="dim")
        for i, loop in enumerate(loops, 1):
            table.add_row(str(i), loop["name"], loop.get("description", ""), loop.get("domain", ""))
        console.print(table)

        choice = Prompt.ask(
            "\nSelect a pattern",
            choices=[str(i) for i in range(1, len(loops) + 1)],
        )
        pattern = loops[int(choice) - 1]["name"]
    elif pattern not in pattern_names:
        console.print(f"[red]Pattern '{pattern}' not found.[/red]")
        console.print(f"[yellow]Available: {', '.join(pattern_names)}[/yellow]")
        raise click.Abort()

    # ── Select agent tool ───────────────────────────────────────────
    if not agent_tool:
        if non_interactive:
            agent_tool = "claude-code"
        else:
            console.print()
            for i, tool in enumerate(AGENT_TOOLS, 1):
                console.print(f"  [bold]{i}.[/bold] {tool}")
            choice = Prompt.ask(
                "\nSelect the agent tool",
                choices=[str(i) for i in range(1, len(AGENT_TOOLS) + 1)],
                default="1",
            )
            agent_tool = AGENT_TOOLS[int(choice) - 1]

    # ── Auto-detect stack ───────────────────────────────────────────
    stack_name, detected_cmd, detected_dir = detect_stack(target_dir)

    config_table = Table.grid(padding=(0, 2))
    config_table.add_column(style="bold cyan")
    config_table.add_column()
    
    config_table.add_row("✦ Pattern", f"[bold white]{pattern}[/bold white]")
    config_table.add_row("✦ Project", target_dir)
    config_table.add_row("✦ Agent  ", agent_tool)
    if stack_name:
        config_table.add_row("✦ Stack  ", f"Auto-detected → [green]{stack_name}[/green]")
    else:
        config_table.add_row("✦ Stack  ", "[dim]Unknown / Default[/dim]")
        
    console.print()
    console.print(
        Panel(
            config_table,
            title="[bold magenta]⚡ SETUP CONFIGURATION ⚡[/bold magenta]",
            title_align="left",
            border_style="bright_blue",
            padding=(1, 2),
            expand=False,
        )
    )

    # ── Run the 5 questions ─────────────────────────────────────────
    if non_interactive:
        answers = {
            "test_command": override_map.get("test_command", detected_cmd),
            "test_dir": override_map.get("test_dir", detected_dir),
            "budget": float(override_map.get("budget", DEFAULTS["budget"])),
            "cadence": override_map.get("cadence", DEFAULTS["cadence"]),
            "merge_strategy": override_map.get("merge_strategy", DEFAULTS["merge_strategy"]),
        }
        console.print("\n[dim]  Non-interactive mode — using defaults/overrides.[/dim]")
    else:
        console.print()
        console.print("  [bold yellow]ℹ Answer these 5 questions. Press Enter to accept defaults.[/bold yellow]")

        answers = {}
        answers["test_command"] = override_map.get(
            "test_command", ask_test_command(detected_cmd, target_dir)
        )
        answers["test_dir"] = override_map.get(
            "test_dir", ask_test_dir(detected_dir, target_dir)
        )
        answers["cadence"] = override_map.get(
            "cadence", ask_cadence()
        )
        answers["budget"] = float(
            override_map.get(
                "budget",
                str(ask_budget(answers["cadence"])),
            )
        )
        answers["merge_strategy"] = override_map.get(
            "merge_strategy", ask_merge_strategy()
        )

    # ── Fetch templates and compile ─────────────────────────────────
    console.print()
    console.rule("[bold]Writing files…[/bold]")

    dest_dir = os.path.join(target_dir, ".loops", pattern)

    try:
        loop_md_template = fetch_file(pattern, "LOOP.md")
        skill_md = fetch_file(pattern, "SKILL.md")
    except Exception as exc:
        console.print(f"[red]Failed to fetch pattern files: {exc}[/red]")
        raise click.Abort()

    loop_md = build_loop_md(pattern, answers, loop_md_template)
    state_md = build_state_md(pattern)
    workflow = build_workflow_yml(pattern, answers["cadence"], agent_tool)

    # ── Prepare file map ────────────────────────────────────────────
    files_to_write = {
        os.path.join(dest_dir, "LOOP.md"): loop_md,
        os.path.join(dest_dir, "SKILL.md"): skill_md,
        os.path.join(dest_dir, "STATE.md"): state_md,
        os.path.join(target_dir, ".github", "workflows", f"{pattern}.yml"): workflow,
    }

    # ── Atomic write ────────────────────────────────────────────────
    atomic_write_files(files_to_write)

    for path_str in files_to_write:
        rel = os.path.relpath(path_str, target_dir)
        console.print(f"  [green]✔[/green] {rel}")

    # ── Done ────────────────────────────────────────────────────────
    completion_lines = []
    completion_lines.append("[bold white]Your loop is successfully configured. Follow these commands to start:[/bold white]\n")
    
    completion_lines.append("  [bold cyan]1. Test the Setup (Safe / Dry-run)[/bold cyan]")
    completion_lines.append(f"     $ [bold]{agent_tool} /loop {pattern} --dry-run[/bold]")
    completion_lines.append("     [dim]Verifies the configuration without writing any persistent changes.[/dim]\n")
    
    completion_lines.append("  [bold cyan]2. Run the Loop[/bold cyan]")
    completion_lines.append(f"     $ [bold]{agent_tool} /loop {pattern}[/bold]")
    completion_lines.append("     [dim]Starts the autonomous fix-verify cycle on the codebase.[/dim]\n")
    
    completion_lines.append("  [bold cyan]3. Monitor Loop Status[/bold cyan]")
    completion_lines.append(f"     $ [bold]loop-wizard status {pattern}[/bold]")
    completion_lines.append("     [dim]Displays real-time execution statistics and state details.[/dim]\n")
    
    completion_lines.append("  [bold cyan]4. Automate on GitHub Actions[/bold cyan]")
    completion_lines.append(f"     $ [bold]git add .loops/ .github/ && git commit -m \"add {pattern} loop\" && git push[/bold]")
    completion_lines.append("     [dim]Schedules the loop to run automatically via GitHub workflows.[/dim]")
    
    completion_panel = Panel(
        "\n".join(completion_lines),
        title="[bold green]✦ L O O P   S U C C E S S F U L L Y   S C A F F O L D E D ✦[/bold green]",
        title_align="center",
        border_style="green",
        padding=(1, 2),
        expand=False,
    )
    
    console.print()
    console.print(completion_panel)
    console.print()
