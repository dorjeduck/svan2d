"""Persistent and in-memory caching for glyph SVG paths."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from .glyph_extractor import extract_glyph_outline, load_font
from .glyph_to_svg_path import glyph_outline_to_svg_path


@dataclass
class CachedGlyph:
    """Cached glyph data."""

    path: str  # SVG path d attribute
    advance_width: float


class GlyphCache:
    """Two-level cache for glyph SVG paths.

    Level 1: In-memory LRU cache (fast, per-session)
    Level 2: Disk cache in ~/.cache/svan2d/fonts/ (persistent)

    Cache files are named by font file hash, so cache invalidates
    automatically when the font file changes.
    """

    CACHE_DIR = Path.home() / ".cache" / "svan2d" / "fonts"
    CACHE_VERSION = 1

    def __init__(self):
        self._memory_cache: Dict[str, Dict[str, CachedGlyph]] = {}
        self._font_hashes: Dict[str, str] = {}
        self._ensure_cache_dir()

    def _ensure_cache_dir(self) -> None:
        """Create cache directory if it doesn't exist."""
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _get_font_hash(self, font_path: str) -> str:
        """Get or compute hash of font file."""
        if font_path in self._font_hashes:
            return self._font_hashes[font_path]

        # Hash font file content
        hasher = hashlib.sha256()
        with open(font_path, "rb") as f:
            # Read in chunks for large files
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)

        font_hash = hasher.hexdigest()[:16]  # Use first 16 chars
        self._font_hashes[font_path] = font_hash
        return font_hash

    def _get_cache_path(self, font_path: str) -> Path:
        """Get the cache file path for a font."""
        font_hash = self._get_font_hash(font_path)
        font_name = Path(font_path).stem.replace(" ", "_")
        return self.CACHE_DIR / f"{font_name}_{font_hash}.json"

    def _load_disk_cache(self, font_path: str) -> Optional[Dict[str, CachedGlyph]]:
        """Load cache from disk if it exists and is valid."""
        cache_path = self._get_cache_path(font_path)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r") as f:
                data = json.load(f)

            # Validate cache version
            if data.get("version") != self.CACHE_VERSION:
                return None

            # Validate font hash
            if data.get("font_hash") != self._get_font_hash(font_path):
                return None

            # Convert to CachedGlyph objects
            glyphs = {}
            for char, glyph_data in data.get("glyphs", {}).items():
                glyphs[char] = CachedGlyph(
                    path=glyph_data["path"],
                    advance_width=glyph_data["advance_width"],
                )

            return glyphs

        except (json.JSONDecodeError, KeyError, TypeError):
            # Invalid cache file - will be regenerated
            return None

    def _save_disk_cache(self, font_path: str, glyphs: Dict[str, CachedGlyph]) -> None:
        """Save cache to disk."""
        cache_path = self._get_cache_path(font_path)

        data = {
            "version": self.CACHE_VERSION,
            "font_hash": self._get_font_hash(font_path),
            "font_path": font_path,
            "created": datetime.now().isoformat(),
            "glyphs": {
                char: {
                    "path": glyph.path,
                    "advance_width": glyph.advance_width,
                }
                for char, glyph in glyphs.items()
            },
        }

        try:
            with open(cache_path, "w") as f:
                json.dump(data, f, indent=2)
        except OSError:
            # Cache write failed - not critical
            pass

    def _get_font_cache(self, font_path: str) -> Dict[str, CachedGlyph]:
        """Get or create the glyph cache for a font."""
        if font_path not in self._memory_cache:
            # Try loading from disk
            disk_cache = self._load_disk_cache(font_path)
            if disk_cache is not None:
                self._memory_cache[font_path] = disk_cache
            else:
                self._memory_cache[font_path] = {}

        return self._memory_cache[font_path]

    def get_glyph(
        self,
        font_path: str,
        char: str,
        font: Optional[object] = None,
    ) -> CachedGlyph:
        """Get glyph SVG path, using cache if available.

        Args:
            font_path: Path to the font file
            char: Single character to get
            font: Optional pre-loaded TTFont object (for performance)

        Returns:
            CachedGlyph with path and advance_width
        """
        cache = self._get_font_cache(font_path)

        if char in cache:
            return cache[char]

        # Not in cache - extract and convert
        if font is None:
            font = load_font(font_path)

        outline = extract_glyph_outline(font, char)
        path = glyph_outline_to_svg_path(outline, scale=1.0, flip_y=True)

        glyph = CachedGlyph(path=path, advance_width=outline.advance_width)

        # Store in memory cache
        cache[char] = glyph

        # Persist to disk
        self._save_disk_cache(font_path, cache)

        return glyph

    def preload_characters(self, font_path: str, characters: str) -> None:
        """Preload a set of characters into cache.

        Useful for preloading common characters (a-z, 0-9, etc.)

        Args:
            font_path: Path to the font file
            characters: String of characters to preload
        """
        font = load_font(font_path)
        for char in characters:
            try:
                self.get_glyph(font_path, char, font=font)
            except ValueError:
                # Character not in font - skip
                pass

    def clear_memory_cache(self) -> None:
        """Clear the in-memory cache (disk cache remains)."""
        self._memory_cache.clear()
        self._font_hashes.clear()

    def clear_disk_cache(self, font_path: Optional[str] = None) -> None:
        """Clear disk cache.

        Args:
            font_path: If provided, clear only this font's cache.
                      If None, clear all cached fonts.
        """
        if font_path:
            cache_path = self._get_cache_path(font_path)
            if cache_path.exists():
                cache_path.unlink()
            if font_path in self._memory_cache:
                del self._memory_cache[font_path]
        else:
            # Clear all
            for cache_file in self.CACHE_DIR.glob("*.json"):
                cache_file.unlink()
            self._memory_cache.clear()


# Global cache instance
_glyph_cache: Optional[GlyphCache] = None


def get_glyph_cache() -> GlyphCache:
    """Get the global glyph cache instance."""
    global _glyph_cache
    if _glyph_cache is None:
        _glyph_cache = GlyphCache()
    return _glyph_cache
