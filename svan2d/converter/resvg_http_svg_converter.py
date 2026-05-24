from __future__ import annotations

import time
from typing import TYPE_CHECKING

import requests

from svan2d.config import ConfigKey, get_config
from svan2d.converter.svg_converter import SVGConverter
from svan2d.core.logger import get_logger

if TYPE_CHECKING:
    from svan2d.vscene.vscene import VScene

logger = get_logger()

# Per-process render timing log, populated from X-Render-* response headers.
# Profilers can read this to surface server-side breakdown.
RENDER_TIMINGS: list[dict] = []


class ResvgHttpSvgConverter(SVGConverter):
    """SVGConverter using a long-running resvg HTTP render server.

    Mirrors PlaywrightHttpSvgConverter but talks to the resvg server. PNG only.
    """

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        auto_start: bool | None = None,
    ):
        super().__init__()
        config = get_config()
        self.host = host or config.get(ConfigKey.RESVG_SERVER_HOST, "localhost")
        self.port = port or config.get(ConfigKey.RESVG_SERVER_PORT, 4100)
        self.base_url = f"http://{self.host}:{self.port}/render"

        if auto_start is None:
            self.auto_start = config.get(ConfigKey.RESVG_SERVER_AUTO_START, False)
        else:
            self.auto_start = auto_start

        self._server_checked = False

    def _convert_to_png(
        self,
        scene: VScene,
        output_file: str,
        frame_time: float | None = 0.0,
        width_px: int | None = None,
        height_px: int | None = None,
    ) -> dict:
        assert width_px is not None and height_px is not None
        try:
            svg_content = self._get_write_scaled_svg_content(
                scene, frame_time or 0.0, width_px, height_px, log=False
            )
            if not self._render(svg_content, output_file, width_px, height_px):
                return {"success": False, "error": "resvg http render failed"}
            return {"success": True, "output": output_file}
        except Exception as e:
            logger.error(f"ResvgHttpSvgConverter PNG error: {e}")
            return {"success": False, "error": str(e)}

    def _convert_to_pdf(
        self,
        scene: VScene,
        output_file: str,
        frame_time: float | None = 0.0,
        inch_width: int | None = None,
        inch_height: int | None = None,
    ) -> dict:
        return {
            "success": False,
            "error": "ResvgHttpSvgConverter does not support PDF; use Cairo or Playwright.",
        }

    def _convert_to_webp(
        self,
        scene: VScene,
        output_file: str,
        frame_time: float | None = 0.0,
        width_px: int | None = None,
        height_px: int | None = None,
        quality: int | None = None,
    ) -> dict:
        return {
            "success": False,
            "error": "ResvgHttpSvgConverter does not support WebP; use the Skia converter.",
        }

    def render_svg_to_png(
        self,
        svg_content: str,
        output_path: str,
        width: int,
        height: int,
    ) -> bool:
        return self._render(svg_content, output_path, width, height)

    def _ensure_server_running(self):
        if self._server_checked:
            return

        health_url = f"http://{self.host}:{self.port}/health"
        try:
            resp = requests.get(health_url, timeout=2)
            if resp.status_code == 200:
                self._server_checked = True
                return
        except requests.exceptions.RequestException:
            pass

        if not self.auto_start:
            raise RuntimeError(
                f"Resvg render server is not running at {self.host}:{self.port}. "
                f"Start it with 'svan2d resvg-server start' or enable auto_start in config."
            )

        logger.info("Auto-starting resvg render server...")
        try:
            from svan2d.server.resvg.process_manager import ProcessManager

            manager = ProcessManager(host=self.host, port=self.port)
            if not manager.is_running():
                manager.start()
                time.sleep(2)
                resp = requests.get(health_url, timeout=5)
                if resp.status_code != 200:
                    raise RuntimeError(
                        "Server started but not responding to health check"
                    )
                logger.info("Resvg server auto-started successfully")
            self._server_checked = True
        except Exception as e:
            raise RuntimeError(f"Failed to auto-start resvg server: {e}")

    def _render(
        self,
        svg_content: str,
        output_path: str,
        width: int,
        height: int,
    ) -> bool:
        self._ensure_server_running()

        max_retries = 3
        timeout = 120

        for attempt in range(max_retries):
            t0 = time.time()
            try:
                resp = requests.post(
                    self.base_url,
                    json={
                        "svg": svg_content,
                        "type": "png",
                        "width": width,
                        "height": height,
                    },
                    timeout=timeout,
                )
                resp.raise_for_status()

                with open(output_path, "wb") as f:
                    f.write(resp.content)

                elapsed = time.time() - t0
                server_timings = {
                    k[len("X-Render-") : -len("-Ms")]: v
                    for k, v in resp.headers.items()
                    if k.lower().startswith("x-render-")
                    and k.lower().endswith("-ms")
                }
                payload_kb = resp.headers.get("X-Render-Payload-Kb")
                if server_timings:
                    RENDER_TIMINGS.append(
                        {
                            "type": "png",
                            "client_ms": elapsed * 1000,
                            "payload_kb": float(payload_kb) if payload_kb else None,
                            "server": {k: float(v) for k, v in server_timings.items()},
                        }
                    )
                    parts = " ".join(f"{k}={v}ms" for k, v in server_timings.items())
                    logger.info(
                        f"PNG {output_path} client={elapsed*1000:.1f}ms "
                        f"payload={payload_kb}KB server[{parts}]"
                    )
                else:
                    logger.debug(f"PNG saved to {output_path} in {elapsed:.4f}s")
                return True

            except requests.exceptions.ConnectionError as e:
                logger.error(f"Cannot connect to resvg server at {self.base_url}: {e}")
                return False
            except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout) as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Render timeout (attempt {attempt + 1}/{max_retries}), retrying..."
                    )
                    time.sleep(1)
                    continue
                logger.error(f"Render failed after {max_retries} attempts: {e}")
                return False
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Render error (attempt {attempt + 1}/{max_retries}): {e}, retrying..."
                    )
                    time.sleep(1)
                    continue
                logger.error(f"Render failed: {e}")
                return False

        return False
