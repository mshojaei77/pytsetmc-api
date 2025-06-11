from __future__ import annotations

"""Command-line interface for PyTSETMC API.

This module exposes a small, but extensible, Typer-based CLI so that
`pipx install git+https://github.com/mshojaei77/pytsetmc-api.git` (or any
other form of installation) provides a working ``pytsetmc`` console
script.  The CLI intentionally starts simple and focuses on the most
common developer actions; future commands can be added without breaking
changes, following Typer's straightforward expansion pattern.

Run ``pytsetmc --help`` after installation to see available commands.
"""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich import print

try:
    from pytsetmc_api import TSETMCClient
except ImportError:  # pragma: no cover – helpful when metadata is broken
    print("[red]Unable to import `pytsetmc_api`. Is the package installed correctly?[/red]")
    sys.exit(1)

# ----------------------------------------------------------------------------
# Typer application setup
# ----------------------------------------------------------------------------

app = typer.Typer(add_help_option=True, help="Python CLI client for Tehran Stock Exchange Market Center (TSETMC) data")


@app.command()
def search(query: str = typer.Argument(..., help="Persian name or symbol to search for"),
           output: Optional[Path] = typer.Option(None, "--output", "-o", help="Optional CSV file to store search results")) -> None:
    """Search for stocks by symbol/name and pretty-print the resulting DataFrame.
    
    Example::

        $ pytsetmc search پترول
    """

    client = TSETMCClient()
    df = client.search_stock(query.strip())

    if df.empty:
        print(f"[yellow]No stocks found for '{query}'.[/yellow]")
        raise typer.Exit(code=1)

    print(f"[green]Found {len(df)} stocks for '{query}':[/green]")
    print(df.to_string(max_rows=20, max_cols=None))

    if output is not None:
        df.to_csv(output, index=False)
        print(f"[blue]Results saved to {output.resolve()}[/blue]")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:  # noqa: D401 – Typer callbacks don't need docstrings
    """Entrypoint that shows help when no command is provided."""

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


if __name__ == "__main__":
    app() 