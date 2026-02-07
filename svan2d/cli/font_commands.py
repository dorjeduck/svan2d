"""CLI commands for managing font glyph cache"""

import click

# Default character set for cache warming
DEFAULT_CHARS = (
    "0123456789"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~ "
)


@click.group(name="font")
def font():
    """Manage font glyph cache for TextPathState"""
    pass


@font.command()  # type: ignore[attr-defined]
@click.argument("font_path", type=click.Path(exists=True))
@click.option(
    "--chars",
    "-c",
    default=None,
    help="Characters to cache (default: alphanumeric + punctuation)",
)
def cache(font_path, chars):
    """Pre-build glyph cache for a font file.

    FONT_PATH is the path to a TTF or OTF font file.

    Example:
        svan2d font cache /path/to/Arial.ttf
        svan2d font cache /path/to/Arial.ttf --chars "0123456789"
    """
    try:
        from svan2d.font.glyph_cache import get_glyph_cache
    except ImportError:
        click.echo("✗ fonttools is required. Install with: pip install svan2d[font]", err=True)
        raise click.Abort()

    charset = chars if chars else DEFAULT_CHARS
    cache_instance = get_glyph_cache()

    click.echo(f"Caching {len(charset)} characters from {font_path}...")

    cached_count = 0
    failed_chars = []

    with click.progressbar(charset, label="Processing") as bar:
        for char in bar:
            try:
                cache_instance.get_glyph(font_path, char)
                cached_count += 1
            except ValueError:
                # Character not in font
                failed_chars.append(char)

    click.echo(f"✓ Cached {cached_count} glyphs")
    if failed_chars:
        # Show printable representation of missing chars
        missing = "".join(c if c.isprintable() and c != " " else f"[{ord(c)}]" for c in failed_chars[:20])
        if len(failed_chars) > 20:
            missing += f"... (+{len(failed_chars) - 20} more)"
        click.echo(f"  Skipped {len(failed_chars)} missing characters: {missing}")

    cache_path = cache_instance._get_cache_path(font_path)
    click.echo(f"  Cache file: {cache_path}")


@font.command()  # type: ignore[attr-defined]
@click.argument("font_path", type=click.Path(exists=True), required=False)
@click.option("--all", "-a", "clear_all", is_flag=True, help="Clear all cached fonts")
def clear(font_path, clear_all):
    """Clear glyph cache.

    Clear cache for a specific font, or use --all to clear everything.

    Example:
        svan2d font clear /path/to/Arial.ttf
        svan2d font clear --all
    """
    try:
        from svan2d.font.glyph_cache import get_glyph_cache
    except ImportError:
        click.echo("✗ fonttools is required. Install with: pip install svan2d[font]", err=True)
        raise click.Abort()

    if not font_path and not clear_all:
        click.echo("✗ Specify a font path or use --all to clear all caches", err=True)
        raise click.Abort()

    cache_instance = get_glyph_cache()

    if clear_all:
        cache_files = list(cache_instance.CACHE_DIR.glob("*.json"))
        count = len(cache_files)
        cache_instance.clear_disk_cache()
        click.echo(f"✓ Cleared {count} cached font(s)")
    else:
        cache_path = cache_instance._get_cache_path(font_path)
        if cache_path.exists():
            cache_instance.clear_disk_cache(font_path)
            click.echo(f"✓ Cleared cache for {font_path}")
        else:
            click.echo(f"✗ No cache found for {font_path}")


@font.command(name="list")  # type: ignore[attr-defined]
def list_cache():
    """List cached fonts.

    Shows all fonts currently in the cache with their glyph counts.
    """
    try:
        from svan2d.font.glyph_cache import get_glyph_cache
        import json
    except ImportError:
        click.echo("✗ fonttools is required. Install with: pip install svan2d[font]", err=True)
        raise click.Abort()

    cache_instance = get_glyph_cache()
    cache_dir = cache_instance.CACHE_DIR

    if not cache_dir.exists():
        click.echo("No font cache directory found")
        return

    cache_files = list(cache_dir.glob("*.json"))

    if not cache_files:
        click.echo("No cached fonts found")
        click.echo(f"  Cache directory: {cache_dir}")
        return

    click.echo(f"Cached fonts ({len(cache_files)}):")
    click.echo(f"  Directory: {cache_dir}")
    click.echo()

    total_glyphs = 0
    for cache_file in sorted(cache_files):
        try:
            with open(cache_file) as f:
                data = json.load(f)

            font_path = data.get("font_path", "unknown")
            glyph_count = len(data.get("glyphs", {}))
            created = data.get("created", "unknown")[:10]  # Just date
            total_glyphs += glyph_count

            # Truncate long paths
            display_path = font_path
            if len(display_path) > 50:
                display_path = "..." + display_path[-47:]

            click.echo(f"  {cache_file.name}")
            click.echo(f"    Font: {display_path}")
            click.echo(f"    Glyphs: {glyph_count}, Created: {created}")
            click.echo()

        except (json.JSONDecodeError, KeyError):
            click.echo(f"  {cache_file.name} (invalid)")

    click.echo(f"Total: {total_glyphs} cached glyphs")
