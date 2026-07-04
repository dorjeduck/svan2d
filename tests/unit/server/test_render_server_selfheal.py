"""Tests for the self-healing browser pool in the Playwright render server.

Covers the recovery logic added after a dead-browser outage: a crashed Chromium
subprocess must be detected and relaunched instead of 500ing forever.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

# Both are optional dependencies; render_server imports playwright at module load.
pytest.importorskip("fastapi", reason="fastapi not installed (optional dependency)")
pytest.importorskip("playwright", reason="playwright not installed (optional dependency)")

from svan2d.server.playwright.render_server import BrowserPool


def make_page(closed: bool = False) -> MagicMock:
    page = MagicMock(name="Page")
    page.is_closed.return_value = closed
    page.unroute = AsyncMock()
    page.set_content = AsyncMock()
    page.close = AsyncMock()
    return page


def make_browser(connected: bool = True) -> MagicMock:
    browser = MagicMock(name="Browser")
    browser.is_connected.return_value = connected
    browser.close = AsyncMock()
    browser.new_page = AsyncMock(side_effect=lambda: make_page())
    return browser


def make_pool(max_pages: int = 2) -> tuple[BrowserPool, MagicMock]:
    """Pool wired to a mock Playwright whose launch() yields a fresh live browser."""
    pool = BrowserPool(max_pages=max_pages)
    playwright = MagicMock(name="Playwright")
    playwright.chromium.launch = AsyncMock(side_effect=lambda **kw: make_browser())
    pool._playwright = playwright
    return pool, playwright


def test_is_healthy_reflects_connection_state():
    pool, _ = make_pool()
    assert pool.is_healthy is False  # no browser yet

    pool._browser = make_browser(connected=True)
    assert pool.is_healthy is True

    pool._browser = make_browser(connected=False)
    assert pool.is_healthy is False


def test_ensure_browser_noop_when_connected():
    pool, playwright = make_pool()
    live = make_browser(connected=True)
    pool._browser = live

    asyncio.run(pool._ensure_browser())

    assert pool._browser is live
    playwright.chromium.launch.assert_not_awaited()


def test_ensure_browser_relaunches_dead_browser_and_resets_pool():
    pool, playwright = make_pool()
    dead = make_browser(connected=False)
    pool._browser = dead
    pool._pages_created = 2
    pool._page_pool.put_nowait(make_page())  # stale page bound to the dead browser

    asyncio.run(pool._ensure_browser())

    assert pool._browser is not dead
    assert pool._browser.is_connected() is True
    assert pool._pages_created == 0          # counter reset
    assert pool._page_pool.empty()           # stale pages drained
    dead.close.assert_awaited_once()
    playwright.chromium.launch.assert_awaited_once()


def test_acquire_page_relaunches_after_browser_death():
    pool, playwright = make_pool()
    pool._browser = make_browser(connected=False)
    pool._pages_created = 2

    async def scenario():
        async with pool.acquire_page() as page:
            assert page is not None
            return page

    page = asyncio.run(scenario())

    # A fresh browser was launched and a page created on it.
    playwright.chromium.launch.assert_awaited_once()
    assert pool._browser.is_connected() is True
    # Page reset and returned to the pool for reuse.
    page.unroute.assert_awaited_once()
    assert pool._pages_created == 1
    assert pool._page_pool.qsize() == 1


def test_acquire_page_discards_closed_pooled_page():
    pool, _ = make_pool()
    live = make_browser(connected=True)
    pool._browser = live
    pool._pages_created = 1
    pool._page_pool.put_nowait(make_page(closed=True))  # dead page in the pool

    async def scenario():
        async with pool.acquire_page() as page:
            return page

    page = asyncio.run(scenario())

    # Closed page dropped (decremented), a fresh one created in its place.
    assert page.is_closed() is False
    live.new_page.assert_awaited_once()
    assert pool._pages_created == 1
    assert pool._page_pool.qsize() == 1


def test_acquire_page_closes_page_when_reset_fails():
    pool, _ = make_pool()
    live = make_browser(connected=True)
    pool._browser = live

    bad_page = make_page()
    bad_page.set_content = AsyncMock(side_effect=RuntimeError("page gone"))
    live.new_page = AsyncMock(return_value=bad_page)
    pool._pages_created = 0

    async def scenario():
        async with pool.acquire_page():
            pass

    asyncio.run(scenario())

    # Reset raised -> page closed and counter decremented, nothing leaked.
    bad_page.close.assert_awaited_once()
    assert pool._pages_created == 0
    assert pool._page_pool.empty()


def test_page_recycled_after_render_threshold():
    pool, _ = make_pool()
    live = make_browser(connected=True)
    page = make_page()
    live.new_page = AsyncMock(return_value=page)  # same page reused each render
    pool._browser = live
    pool.max_page_renders = 3

    async def render_once():
        async with pool.acquire_page():
            pass

    for _ in range(2):
        asyncio.run(render_once())

    # Below threshold: reused, still pooled, not closed.
    page.close.assert_not_awaited()
    assert pool._pages_created == 1
    assert pool._page_pool.qsize() == 1

    asyncio.run(render_once())  # 3rd render hits the threshold

    # Recycled: closed, counter decremented, dropped from the pool.
    page.close.assert_awaited_once()
    assert pool._pages_created == 0
    assert pool._page_pool.empty()


def test_recycle_disabled_when_threshold_zero():
    pool, _ = make_pool()
    live = make_browser(connected=True)
    page = make_page()
    live.new_page = AsyncMock(return_value=page)
    pool._browser = live
    pool.max_page_renders = 0  # disabled

    async def render_once():
        async with pool.acquire_page():
            pass

    for _ in range(5):
        asyncio.run(render_once())

    page.close.assert_not_awaited()
    assert pool._pages_created == 1
    assert pool._page_pool.qsize() == 1
