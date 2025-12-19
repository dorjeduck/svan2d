"""SVG path morphing implementations.

Provides morpher classes for smooth path-to-path transitions:
- FlubberMorpher: Shape morphing using flubber.js (via Node.js subprocess)
- NativeMorpher: Native Python stroke-based morphing for open paths
"""

from .flubber_morpher import FlubberMorpher
from .native_morpher import NativeMorpher

__all__ = ["FlubberMorpher", "NativeMorpher"]
