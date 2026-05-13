"""Main CLI entry point for Svan2D.

Commands: serve (dev server), playwright-server, resvg-server, font (glyph cache).
"""

import click

from svan2d.cli.devserver_commands import serve
from svan2d.cli.font_commands import font
from svan2d.cli.playwright_server_commands import playwright_server
from svan2d.cli.resvg_server_commands import resvg_server


@click.group()
@click.version_option(package_name="svan2d")
def cli():
    """Svan2D - Programmatic SVG graphics and animation library"""
    pass


# Register command groups
cli.add_command(font)  # type: ignore[attr-defined]
cli.add_command(playwright_server)  # type: ignore[attr-defined]
cli.add_command(resvg_server)  # type: ignore[attr-defined]
cli.add_command(serve)  # type: ignore[attr-defined]


if __name__ == "__main__":
    cli()
