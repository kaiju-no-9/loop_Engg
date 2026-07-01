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


if __name__ == "__main__":
    cli()
