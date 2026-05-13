"""CLI commands for managing the resvg render server."""

import click

from svan2d.config import ConfigKey, get_config
from svan2d.server.resvg.process_manager import ProcessManager


def get_process_manager() -> ProcessManager:
    config = get_config()
    host = config.get(ConfigKey.RESVG_SERVER_HOST, "localhost")
    port = config.get(ConfigKey.RESVG_SERVER_PORT, 4100)
    return ProcessManager(host=host, port=port)


@click.group(name="resvg-server")
def resvg_server():
    """Manage the resvg render server"""
    pass


@resvg_server.command()  # type: ignore[attr-defined]
def start():
    """Start the resvg render server in the background"""
    manager = get_process_manager()

    if manager.is_running():
        click.echo("✓ Resvg server is already running")
        status = manager.status()
        click.echo(f"  PID: {status['pid']}")
        click.echo(f"  Uptime: {status['uptime_seconds']:.1f}s")
        return

    try:
        manager.start()
        click.echo("✓ Resvg server started successfully")
        click.echo(f"  Host: {manager.host}")
        click.echo(f"  Port: {manager.port}")
        click.echo(f"  PID file: {manager.pid_file}")
        click.echo(f"  Log file: {manager.log_file}")
    except Exception as e:
        click.echo(f"✗ Failed to start server: {e}", err=True)
        raise click.Abort()


@resvg_server.command()  # type: ignore[attr-defined]
def stop():
    """Stop the resvg render server"""
    manager = get_process_manager()

    if not manager.is_running():
        click.echo("✓ Resvg server is not running")
        return

    try:
        manager.stop()
        click.echo("✓ Resvg server stopped successfully")
    except Exception as e:
        click.echo(f"✗ Failed to stop server: {e}", err=True)
        raise click.Abort()


@resvg_server.command()  # type: ignore[attr-defined]
def restart():
    """Restart the resvg render server"""
    manager = get_process_manager()

    try:
        manager.restart()
        click.echo("✓ Resvg server restarted successfully")
        click.echo(f"  Host: {manager.host}")
        click.echo(f"  Port: {manager.port}")
    except Exception as e:
        click.echo(f"✗ Failed to restart server: {e}", err=True)
        raise click.Abort()


@resvg_server.command()  # type: ignore[attr-defined]
def status():
    """Check resvg render server status"""
    manager = get_process_manager()
    status_info = manager.status()

    if status_info["running"]:
        click.echo("✓ Resvg server is running")
        click.echo(f"  PID: {status_info['pid']}")
        click.echo(f"  Uptime: {status_info['uptime_seconds']:.1f}s")
        click.echo(f"  Memory: {status_info['memory_mb']:.1f} MB")
        click.echo(f"  Host: {manager.host}")
        click.echo(f"  Port: {manager.port}")
    else:
        click.echo("✗ Resvg server is not running")
        click.echo(f"  Use 'svan2d resvg-server start' to start it")


@resvg_server.command()  # type: ignore[attr-defined]
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
