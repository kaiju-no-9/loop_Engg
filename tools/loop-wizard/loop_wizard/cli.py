"""Main CLI entrypoint for loop-wizard.

Usage:
    loop-wizard init <target-dir> --pattern <name> --tool <agent>
    loop-wizard audit <dir> [--suggest]
    loop-wizard cost --pattern <name> [--cadence <freq>] [--model <model>]
    loop-wizard dashboard <dir>
    loop-wizard status [loop-name] [--dir <dir>] [--watch] [--json]
"""

import click

from loop_wizard import __version__
from loop_wizard.commands.init import init_cmd
from loop_wizard.commands.audit import audit_cmd
from loop_wizard.commands.cost import cost_cmd
from loop_wizard.commands.dashboard import dashboard_cmd
from loop_wizard.commands.status import status_cmd


@click.group()
@click.version_option(version=__version__, prog_name="loop-wizard")
def cli():
    """Loop Wizard — Unified CLI for Loop Engineering.

    Scaffold, configure, audit, estimate costs, and monitor AI agent loops
    from a single command-line tool.
    """
    pass


cli.add_command(init_cmd, "init")
cli.add_command(audit_cmd, "audit")
cli.add_command(cost_cmd, "cost")
cli.add_command(dashboard_cmd, "dashboard")
cli.add_command(status_cmd, "status")


import sys
from loop_wizard.commands.init import run_init_flow, fetch_registry

@click.group(invoke_without_command=True)
@click.option("--pattern", "-p", help="Name of the loop pattern to scaffold")
@click.option("--list", "list_flag", is_flag=True, help="Print full registry as plain text")
@click.option("--domain", help="Filter --list output to one domain")
@click.option("--json", "json_flag", is_flag=True, help="Format list output as JSON")
@click.pass_context
def loopwiz_cli(ctx, pattern, list_flag, domain, json_flag):
    """Interactive Loop Pattern Picker & CLI for loop initialization."""
    loops = fetch_registry()
    
    if list_flag:
        if domain:
            loops = [l for l in loops if l.get('domain', '').lower() == domain.lower()]
        
        if json_flag:
            import json
            click.echo(json.dumps(loops, indent=2))
        else:
            for l in loops:
                click.echo(f"{l.get('name', '')}\t{l.get('domain', '')}\t{l.get('description', '')}")
        return

    if pattern:
        # direct run via flag
        run_init_flow(target_dir=".", pattern=pattern, agent_tool=None, non_interactive=False, overrides=[], reconfigure=False)
        return
        
    if ctx.invoked_subcommand is None:
        if not sys.stdin.isatty():
            names = [l.get('name', '') for l in loops]
            click.echo("Error: No pattern provided in non-interactive mode.", err=True)
            click.echo(f"Available patterns: {', '.join(names)}", err=True)
            sys.exit(1)
            
        from loop_wizard.commands.picker import run_picker
        selected = run_picker(loops)
        if not selected:
            sys.exit(0)
        run_init_flow(target_dir=".", pattern=selected, agent_tool=None, non_interactive=False, overrides=[], reconfigure=False)


@loopwiz_cli.command("run")
@click.argument("pattern_name")
def loopwiz_run(pattern_name):
    """Run a pattern directly by exact name."""
    loops = fetch_registry()
    names = [l.get('name', '') for l in loops]
    if pattern_name not in names:
        import difflib
        matches = difflib.get_close_matches(pattern_name, names, n=3, cutoff=0.3)
        click.echo(f"Error: Pattern '{pattern_name}' not found.", err=True)
        if matches:
            click.echo(f"Did you mean: {', '.join(matches)}?", err=True)
        sys.exit(1)
        
    run_init_flow(target_dir=".", pattern=pattern_name, agent_tool=None, non_interactive=False, overrides=[], reconfigure=False)


if __name__ == "__main__":
    cli()
