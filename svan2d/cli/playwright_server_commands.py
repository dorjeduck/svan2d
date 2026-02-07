"""CLI commands for managing the Playwright render server"""

import click

from svan2d.config import ConfigKey, get_config
from svan2d.server.playwright.process_manager import ProcessManager


def get_process_manager(max_pages: int | None = None) -> ProcessManager:
    """Create ProcessManager with config settings"""
    config = get_config()
    host = config.get(ConfigKey.PLAYWRIGHT_SERVER_HOST, "localhost")
    port = config.get(ConfigKey.PLAYWRIGHT_SERVER_PORT, 4000)
    if max_pages is None:
        max_pages = config.get(ConfigKey.PLAYWRIGHT_SERVER_MAX_PAGES, 4)
    assert max_pages is not None
    return ProcessManager(host=host, port=port, max_pages=max_pages)


@click.group(name="playwright-server")
def playwright_server():
    """Manage the Playwright render server"""
    pass


@playwright_server.command()  # type: ignore[attr-defined]
@click.option(
    "--max-pages",
    "-p",
    default=None,
    type=int,
    help="Max browser pages in pool (default: from config)",
)
def start(max_pages):
    """Start the Playwright render server in the background"""
    manager = get_process_manager(max_pages=max_pages)

    if manager.is_running():
        click.echo("✓ Playwright server is already running")
        click.echo("  Stop it first to change max-pages setting")
        status = manager.status()
        click.echo(f"  PID: {status['pid']}")
        click.echo(f"  Uptime: {status['uptime_seconds']:.1f}s")
        return

    try:
        manager.start()
        click.echo("✓ Playwright server started successfully")
        click.echo(f"  Host: {manager.host}")
        click.echo(f"  Port: {manager.port}")
        click.echo(f"  Max pages: {manager.max_pages}")
        click.echo(f"  PID file: {manager.pid_file}")
        click.echo(f"  Log file: {manager.log_file}")
    except Exception as e:
        click.echo(f"✗ Failed to start server: {e}", err=True)
        raise click.Abort()


@playwright_server.command()  # type: ignore[attr-defined]
def stop():
    """Stop the Playwright render server"""
    manager = get_process_manager()

    if not manager.is_running():
        click.echo("✓ Playwright server is not running")
        return

    try:
        manager.stop()
        click.echo("✓ Playwright server stopped successfully")
    except Exception as e:
        click.echo(f"✗ Failed to stop server: {e}", err=True)
        raise click.Abort()


@playwright_server.command()  # type: ignore[attr-defined]
@click.option(
    "--max-pages",
    "-p",
    default=None,
    type=int,
    help="Max browser pages in pool (default: from config)",
)
def restart(max_pages):
    """Restart the Playwright render server"""
    manager = get_process_manager(max_pages=max_pages)

    try:
        manager.restart()
        click.echo("✓ Playwright server restarted successfully")
        click.echo(f"  Host: {manager.host}")
        click.echo(f"  Port: {manager.port}")
        click.echo(f"  Max pages: {manager.max_pages}")
    except Exception as e:
        click.echo(f"✗ Failed to restart server: {e}", err=True)
        raise click.Abort()


@playwright_server.command()  # type: ignore[attr-defined]
def status():
    """Check Playwright render server status"""
    manager = get_process_manager()
    status_info = manager.status()

    if status_info["running"]:
        click.echo("✓ Playwright server is running")
        click.echo(f"  PID: {status_info['pid']}")
        click.echo(f"  Uptime: {status_info['uptime_seconds']:.1f}s")
        click.echo(f"  Memory: {status_info['memory_mb']:.1f} MB")
        click.echo(f"  Host: {manager.host}")
        click.echo(f"  Port: {manager.port}")
    else:
        click.echo("✗ Playwright server is not running")
        click.echo(f"  Use 'svan2d playwright-server start' to start it")


@playwright_server.command()  # type: ignore[attr-defined]
@click.option("--lines", "-n", default=50, help="Number of log lines to show")
def logs(lines):
    """Show recent server logs"""
    manager = get_process_manager()
    log_content = manager.get_logs(lines=lines)

    if "No log file found" in log_content or "Error reading" in log_content:
        click.echo(f"✗ {log_content}", err=True)
    else:
        click.echo(f"Last {lines} lines from {manager.log_file}:")
        click.echo("=" * 80)
        click.echo(log_content)
