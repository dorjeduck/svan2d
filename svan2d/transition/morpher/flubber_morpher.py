"""
Flubber-based shape morphing with Node.js bridge.

This module provides shape interpolation using the Flubber JavaScript library,
communicating via a persistent Node.js subprocess.
"""

import hashlib
import json
import logging
import os
import subprocess
from typing import Any, Dict, Optional, Tuple

from svan2d.path import SVGPath
from svan2d.transition.morpher.base_morpher import BaseMorpher

logger = logging.getLogger(__name__)


def _hash_shape(shape_str: str) -> str:
    """Create hash of path string for caching."""
    return hashlib.md5(shape_str.encode()).hexdigest()


class FlubberNodeBridge:
    """
    Persistent Flubber interpolator that keeps Node.js process alive.
    Call it repeatedly with different t values efficiently.
    """

    def __init__(
        self, shape1: str, shape2: str, flubber_path=None, node_modules_path=None
    ):
        """
        Create interpolator between two shapes.

        Args:
            shape1: SVG path string
            shape2: SVG path string
            flubber_path: Path to flubber installation directory (optional)
            node_modules_path: Direct path to node_modules folder (optional)
        """
        self.shape1 = shape1
        self.shape2 = shape2
        self.flubber_path = flubber_path
        self.node_modules_path = node_modules_path
        self.process = None
        self._start_process()

    def _find_node_modules(self) -> Optional[str]:
        """Find node_modules directory."""
        if self.node_modules_path:
            if not os.path.isdir(self.node_modules_path):
                raise FileNotFoundError(
                    f"Specified node_modules path does not exist: {self.node_modules_path}"
                )
            flubber_module = os.path.join(self.node_modules_path, "flubber")
            if not os.path.isdir(flubber_module):
                raise FileNotFoundError(
                    f"Flubber not found in: {self.node_modules_path}\n"
                    f"Install it with: cd {os.path.dirname(self.node_modules_path)} && npm install flubber"
                )
            return self.node_modules_path

        search_paths = []

        if self.flubber_path:
            if not os.path.isdir(self.flubber_path):
                raise FileNotFoundError(
                    f"Specified flubber_path does not exist: {self.flubber_path}"
                )
            search_paths.append(self.flubber_path)

        # Add current directory and up to 5 parent directories
        current = os.getcwd()
        for _ in range(6):
            search_paths.append(current)
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent

        # Check each path for node_modules
        for path in search_paths:
            node_modules = os.path.join(path, "node_modules")
            flubber_module = os.path.join(node_modules, "flubber")
            if os.path.isdir(flubber_module):
                return node_modules

        return None

    def _start_process(self):
        """Start persistent Node.js process."""
        script = """
        const flubber = require('flubber');
        const readline = require('readline');

        const rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout
        });

        let interpolator = null;

        rl.on('line', (line) => {
            try {
                const msg = JSON.parse(line);

                if (msg.command === 'setup') {
                    interpolator = flubber.interpolate(msg.shape1, msg.shape2,{ maxSegmentLength: 0.5 } );
                    console.log(JSON.stringify({status: 'ready'}));
                }
                else if (msg.command === 'interpolate') {
                    if (!interpolator) {
                        console.log(JSON.stringify({error: 'Not initialized'}));
                    } else {
                        const result = interpolator(msg.t);
                        console.log(JSON.stringify({result: result}));
                    }
                }
                else if (msg.command === 'exit') {
                    process.exit(0);
                }
            } catch (e) {
                console.log(JSON.stringify({error: e.message}));
            }
        });
        """

        # Prepare environment
        env = os.environ.copy()
        node_modules = None

        try:
            node_modules = self._find_node_modules()
        except FileNotFoundError as e:
            raise RuntimeError(str(e)) from e

        if node_modules:
            node_path = env.get("NODE_PATH", "")
            if node_path:
                env["NODE_PATH"] = f"{node_modules}{os.pathsep}{node_path}"
            else:
                env["NODE_PATH"] = node_modules

        try:
            self.process = subprocess.Popen(
                ["node", "-e", script],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                env=env,
                cwd=self.flubber_path if self.flubber_path else None,
            )
        except FileNotFoundError:
            raise RuntimeError(
                "Node.js not found!\n"
                "Please install Node.js from: https://nodejs.org/\n"
                "Or install via package manager:\n"
                "  - Mac: brew install node\n"
                "  - Ubuntu/Debian: sudo apt install nodejs npm\n"
                "  - Windows: Download from nodejs.org"
            )

        # Setup interpolator
        self._send_command(
            {"command": "setup", "shape1": self.shape1, "shape2": self.shape2}
        )

        try:
            response = self._read_response()
        except json.JSONDecodeError:
            assert self.process is not None and self.process.stderr is not None
            stderr_output = self.process.stderr.read()

            if "Cannot find module 'flubber'" in stderr_output:
                search_info = [f"  - Current directory: {os.getcwd()}/node_modules"]
                if self.node_modules_path:
                    search_info.insert(
                        0, f"  - Specified path: {self.node_modules_path}"
                    )
                elif self.flubber_path:
                    search_info.insert(
                        0, f"  - Specified path: {self.flubber_path}/node_modules"
                    )
                search_info.append("  - Global npm modules")

                raise RuntimeError(
                    "Flubber JavaScript library not found!\n\n"
                    "Searched in:\n" + "\n".join(search_info) + "\n\n"
                    "To fix this, install Flubber:\n\n"
                    "Option 1 - Install locally (recommended):\n"
                    f"  cd {os.getcwd()}\n"
                    "  npm install flubber\n\n"
                    "Option 2 - Install globally:\n"
                    "  npm install -g flubber\n\n"
                    "Option 3 - Specify custom path:\n"
                    "  FlubberMorpher(shape1, shape2, flubber_path='/your/path')"
                )
            else:
                raise RuntimeError(
                    f"Failed to initialize Flubber.\n"
                    f"Node.js error:\n{stderr_output}"
                )

        if response.get("status") != "ready":
            error_msg = (
                self.process.stderr.read() if self.process.stderr else "Unknown error"
            )
            raise RuntimeError(
                f"Failed to initialize Flubber interpolator.\n"
                f"Response: {response}\n"
                f"Error output: {error_msg}"
            )

    def _send_command(self, cmd: dict):
        """Send command to Node.js process."""
        assert self.process is not None and self.process.stdin is not None
        self.process.stdin.write(json.dumps(cmd) + "\n")
        self.process.stdin.flush()

    def _read_response(self) -> dict:
        """Read response from Node.js process."""
        assert self.process is not None and self.process.stdout is not None
        line = self.process.stdout.readline()
        return json.loads(line)

    def interpolate(self, t: float) -> str:
        """
        Get interpolated shape at t value.

        Args:
            t: Float between 0.0 and 1.0

        Returns:
            SVG path string
        """
        self._send_command({"command": "interpolate", "t": t})
        response = self._read_response()

        if "error" in response:
            raise RuntimeError(f"Interpolation error: {response['error']}")

        return response["result"]

    def close(self):
        """Close the Node.js process."""
        if self.process:
            try:
                self._send_command({"command": "exit"})
                self.process.wait(timeout=1)
            except Exception:
                self.process.kill()
            finally:
                self.process = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.close()


class FlubberMorpher(BaseMorpher):
    """
    Flubber-based shape interpolator with reference-counted caching.

    Uses the static 'for_paths' factory method to manage a global instance cache.
    Multiple calls to for_paths() with the same shapes return the same instance,
    and the instance is only cleaned up when all references call close().
    """

    # --- Global Class Attributes ---
    _morpher_cache: Dict[Tuple[str, str, str], "FlubberMorpher"] = {}
    _reference_counts: Dict[Tuple[str, str, str], int] = {}

    @classmethod
    def for_paths(
        cls, path1: SVGPath, path2: SVGPath, **kwargs: Any
    ) -> "FlubberMorpher":
        """
        Factory method that returns a cached morpher instance.

        Multiple calls with the same paths (and kwargs) return the same instance.
        Each call increments a reference count. Call close() when done to decrement.

        Args:
            path1: Start shape
            path2: End shape
            **kwargs: Options passed to FlubberNodeBridge (e.g., flubber_path)

        Returns:
            FlubberMorpher instance (possibly cached)
        """
        key1 = _hash_shape(path1.to_string())
        key2 = _hash_shape(path2.to_string())
        # Include kwargs in cache key to handle different options
        kwargs_key = json.dumps(kwargs, sort_keys=True) if kwargs else ""
        cache_key = (key1, key2, kwargs_key)

        # Check cache
        if cache_key not in cls._morpher_cache:
            # Cache miss: create new instance
            morpher = cls(path1, path2, cache_key=cache_key, **kwargs)
            cls._morpher_cache[cache_key] = morpher
            cls._reference_counts[cache_key] = 0

        # Increment reference count
        cls._reference_counts[cache_key] += 1

        return cls._morpher_cache[cache_key]

    def __init__(
        self,
        path1: SVGPath,
        path2: SVGPath,
        cache_key: Tuple[str, str, str],
        max_cache_size: int | None = None,
        **kwargs: Any,
    ):
        """
        Constructor. Executes the expensive Node.js bridge initialization.

        Note: This should only be called via for_paths(), not directly.

        Args:
            path1: Start shape
            path2: End shape
            cache_key: Tuple used for cache lookup
            **kwargs: Options for FlubberNodeBridge
        """
        # Initialize base class (sets self.path1, self.path2, self._cache)
        super().__init__(path1, path2, **kwargs)

        # Store cache key for reference counting
        self._cache_key = cache_key
        self._is_closed = False

        # Initialize the Node.js process
        self._bridge = FlubberNodeBridge(
            self.path1.to_string(), self.path2.to_string(), **kwargs
        )

    def __call__(self, t: float) -> SVGPath:
        """
        Calculates the interpolated shape at t (0.0 to 1.0).

        Args:
            t: Interpolation factor

        Returns:
            Interpolated SVGPath

        Raises:
            RuntimeError: If morpher has been fully closed
        """
        if self._is_closed:
            raise RuntimeError(
                "Cannot interpolate: this morpher has been closed. "
                "All references have called close()."
            )

        def core_interpolation(t_val):
            shape_string = self._bridge.interpolate(t_val)
            return SVGPath.from_string(shape_string)

        return self._interpolate_with_caching(t, core_interpolation)

    def close(self):
        """
        Decrement reference count and cleanup if this is the last reference.

        Safe to call multiple times. Only closes the Node.js process when
        all references have called close().
        """
        # Skip if already fully closed
        if self._is_closed:
            return

        # Decrement reference count
        if self._cache_key in self._reference_counts:
            self._reference_counts[self._cache_key] -= 1

            # Only truly close when no references remain
            if self._reference_counts[self._cache_key] <= 0:
                self._actually_close()

    def _actually_close(self):
        """Internal method that performs the actual cleanup."""
        # Close the Node.js process
        if self._bridge:
            self._bridge.close()

        # Clear the t-value cache
        self._cache.clear()

        # Remove from global caches
        if self._cache_key in self._morpher_cache:
            del self._morpher_cache[self._cache_key]
        if self._cache_key in self._reference_counts:
            del self._reference_counts[self._cache_key]

        # Mark as closed
        self._is_closed = True

    @classmethod
    def cleanup(cls):
        """
        Force cleanup of all cached morphers regardless of reference counts.

        Use this for emergency cleanup or at application shutdown.
        Does not affect reference counts - resets everything.
        """
        for morpher in list(cls._morpher_cache.values()):
            if not morpher._is_closed:
                morpher._actually_close()

        cls._morpher_cache.clear()
        cls._reference_counts.clear()

    @classmethod
    def clear_morpher_cache(cls):
        """Alias for cleanup(). Clear all cached morphers."""
        cls.cleanup()

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support - calls close() on exit."""
        self.close()
        return False

    def __del__(self):
        """Destructor - ensure cleanup happens."""
        if not self._is_closed:
            self.close()

    @classmethod
    def cache_stats(cls) -> Dict[str, Any]:
        """
        Get statistics about the global morpher cache.

        Returns:
            Dict with cache size, active instances, total references
        """
        return {
            "cached_instances": len(cls._morpher_cache),
            "total_references": sum(cls._reference_counts.values()),
            "instances": [
                {
                    "cache_key": f"{key[0][:8]}...{key[1][:8]}",
                    "references": cls._reference_counts[key],
                    "t_cache_size": len(cls._morpher_cache[key]._cache),
                    "t_cache_stats": cls._morpher_cache[key].get_cache_stats(),
                }
                for key in cls._morpher_cache
            ],
        }
