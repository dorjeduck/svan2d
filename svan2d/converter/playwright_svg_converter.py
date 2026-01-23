from __future__ import annotations

import time
import traceback
from typing import TYPE_CHECKING, Optional

from playwright.sync_api import sync_playwright

from svan2d.converter.svg_converter import SVGConverter
from svan2d.core.logger import get_logger

if TYPE_CHECKING:
    from svan2d.vscene.vscene import VScene

logger = get_logger()


class PlaywrightSvgConverter(SVGConverter):
    """
    SVGConverter implementation using Playwright for conversions.
    """

    def _convert(
        self,
        scene: VScene,
        output: dict,
        frame_time: Optional[float] = 0.0,
        formats: Optional[list] = ["png", "pdf"],
        png_width_px: int | None = None,
        png_height_px: int | None = None,
        pdf_inch_width: float | None = None,
        pdf_inch_height: float | None = None,
    ) -> dict:
        """
        Export both PNG and PDF in a single Chromium session.
        """
        if formats is None:
            formats = ["png", "pdf"]
        if frame_time is None:
            frame_time = 0.0
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
                context = browser.new_context()
                ret = {}

                def render_page(width: int, height: int, content: str):
                    page = context.new_page()
                    page.set_viewport_size({"width": width, "height": height})
                    page.set_content(self.svg_html(content))
                    page.wait_for_load_state("networkidle")
                    return page

                # PNG
                if "png" in formats:
                    t0 = time.time()
                    width_px, height_px = self._infer_dimensions(
                        scene, png_width_px, png_height_px
                    )
                    logger.debug(f"Rendering PNG with size {width_px}x{height_px}")

                    svg_content = self._get_write_scaled_svg_content(
                        scene, frame_time, width_px, height_px
                    )
                    page = render_page(width_px, height_px, svg_content)
                    page.screenshot(path=output["png"], full_page=True)
                    page.close()
                    elapsed = time.time() - t0
                    ret["png"] = output["png"]
                    logger.debug(
                        f"PNG exported to {output['png']} (PlaywrightSvgConverter) in {elapsed:.4f} seconds"
                    )

                # PDF
                if "pdf" in formats and pdf_inch_width and pdf_inch_height:
                    t0 = time.time()
                    # Viewport for rendering in pixels
                    width_px = int(pdf_inch_width * 96)
                    height_px = int(pdf_inch_height * 96)
                    width_px, height_px = self._infer_dimensions(
                        scene, width_px, height_px
                    )
                    svg_content = self._get_write_scaled_svg_content(
                        scene, frame_time, width_px, height_px
                    )
                    page = render_page(width_px, height_px, svg_content)
                    page.pdf(
                        path=output["pdf"],
                        width=f"{pdf_inch_width}in",
                        height=f"{pdf_inch_height}in",
                        margin={
                            "top": "0px",
                            "bottom": "0px",
                            "left": "0px",
                            "right": "0px",
                        },
                        print_background=True,
                    )
                    page.close()
                    elapsed = time.time() - t0
                    ret["pdf"] = output["pdf"]
                    logger.debug(
                        f"PDF exported to {output['pdf']} (PlaywrightSvgConverter) in {elapsed:.4f} seconds"
                    )

                browser.close()
                ret["success"] = True
                return ret

        except Exception as e:
            traceback.print_exc()
            logger.error(f"PlaywrightSvgConverter error: {e}")
            return {"success": False, "error": str(e)}

    def _convert_to_png(self, *args, **kwargs) -> dict:
        # not called, handled by _convert
        return {}

    def _convert_to_pdf(self, *args, **kwargs) -> dict:
        # not called, handled by _convert
        return {}
