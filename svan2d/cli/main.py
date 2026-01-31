"""Main CLI entry point for Svan2D

Provides commands for managing the Playwright render server and other utilities.
"""

import click

from svan2d.cli.devserver_commands import serve
from svan2d.cli.font_commands import font
from svan2d.cli.playwright_server_commands import playwright_server


@click.group()
@click.version_option(package_name="svan2d")
def cli():
    """Svan2D - Programmatic SVG graphics and animation library"""
    pass


# Register command groups
cli.add_command(font)  # type: ignore[attr-defined]
cli.add_command(playwright_server)  # type: ignore[attr-defined]
cli.add_command(serve)  # type: ignore[attr-defined]


if __name__ == "__main__":
    cli()
