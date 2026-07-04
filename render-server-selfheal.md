# Render server: dead-browser outage & self-heal fix

**Component:** `svan2d/server/playwright/render_server.py` (FastAPI + Playwright,
`localhost:4000`, systemd unit `svan2d-playwright.service`).

**Symptom (2026-07-04):** Every `POST /render` returned `500 Server Error`.
The uvicorn process was alive and `Restart=always` never fired because the
*process* never exited. `GET /health` still reported `{"status":"ok"}`.
`GET /stats` showed `pages_created: 0, pages_available: 0`. A `systemctl
restart` fixed it immediately.

Downstream this cascaded: `social_img_cli` got a render result with no `png`
key → the WordPress social plugin passed a `null` image path to every gateway
→ Facebook's Python gateway crashed on `os.path.abspath(None)`, the others
silently no-op'd. **Nothing posted.** The render server is the root cause; the
social side just had no guard against a null path.

---

## Root cause

The persistent Chromium browser died (crash/OOM of the browser subprocess — the
unit has an OOM-kill history). The FastAPI process kept running but held a dead
`Browser` handle, and **nothing in the code ever detects or recovers from a dead
browser.** Three distinct defects:

### 1. No browser liveness check / no relaunch
`BrowserPool.start()` launches Chromium exactly once. Nothing ever calls
`browser.is_connected()` or relaunches it. Once the browser dies,
`acquire_page()` keeps calling `self._browser.new_page()` (line ~78) on a dead
handle → raises → bubbles to the `/render` handler → 500, forever.

### 2. The page pool drains itself to zero and stays there
In `acquire_page()`'s `finally` block (lines ~88–98): when a page can't be
reset (because its browser is dead) it decrements `_pages_created` and discards
the page — but never `close()`s it and never checks the browser. After the
browser dies, each in-flight request drives the counter down until
`pages_created == 0`. From then on every request tries `new_page()` on the dead
browser and 500s. This is exactly the `pages_created: 0` we observed.

### 3. `/health` lies
`health_check()` returns `{"status":"ok"}` unconditionally. It never inspects
the browser, so no external monitor — and no systemd health probe — can tell the
server is broken. Combined with `Type=forking` + `Restart=always` (which only
reacts to *process* exit), the broken-but-alive state is invisible.

---

## Failure chain

```
Chromium browser subprocess dies (crash / OOM)
  → self._browser handle is now disconnected, process stays up
  → acquire_page(): reset fails in finally → pages_created-- (page never closed)
  → repeat until pages_created == 0
  → every new_page() raises → /render returns 500 (permanently)
  → /health still returns 200 {"status":"ok"}  ← nobody notices
  → systemd Restart=always never triggers (process never exited)
```

---

## Solution

Two independent layers. Layer A is the real fix (in svan2d); Layer B is a
cheap backstop. Do both.

### Layer A — make the pool self-healing (`render_server.py`)

**A1. Add a browser-liveness guard + relaunch.** New method on `BrowserPool`,
called at the top of every `acquire_page()`:

```python
async def _ensure_browser(self):
    """Relaunch the browser (and reset the pool) if it has died."""
    if self._browser is not None and self._browser.is_connected():
        return
    async with self._lock:
        # Re-check under lock; another coroutine may have healed it.
        if self._browser is not None and self._browser.is_connected():
            return
        logger.warning("Browser is down — relaunching pool")
        if self._browser is not None:
            try:
                await self._browser.close()
            except Exception:
                pass
        # Drain now-dead pages and reset the counter.
        while not self._page_pool.empty():
            try:
                self._page_pool.get_nowait()
            except asyncio.QueueEmpty:
                break
        self._pages_created = 0
        if self._playwright is None:
            self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        logger.info("Browser relaunched")
```

**A2. Validate pooled pages and close dead ones.** In `acquire_page()`:
- Call `await self._ensure_browser()` before acquiring.
- After pulling a page from the pool, if `page.is_closed()` → drop it
  (`self._pages_created -= 1` under lock) and get/create another.
- In the `finally`, when reset fails, `await page.close()` (best-effort) before
  decrementing, so orphaned pages don't leak.

Reference shape:

```python
@asynccontextmanager
async def acquire_page(self):
    await self._ensure_browser()
    page = None
    try:
        while page is None:
            try:
                candidate = self._page_pool.get_nowait()
            except asyncio.QueueEmpty:
                candidate = None
            if candidate is not None:
                if candidate.is_closed():
                    async with self._lock:
                        self._pages_created -= 1
                    continue
                page = candidate
                break
            async with self._lock:
                if self._pages_created < self.max_pages:
                    page = await self._browser.new_page()
                    self._pages_created += 1
            if page is None:                      # pool full, wait for a return
                page = await self._page_pool.get()
                if page.is_closed():
                    async with self._lock:
                        self._pages_created -= 1
                    page = None
        yield page
    finally:
        if page is not None:
            try:
                if page.is_closed():
                    async with self._lock:
                        self._pages_created -= 1
                else:
                    await page.unroute("**/*")
                    await page.set_content("<html><body></body></html>")
                    await self._page_pool.put(page)
            except Exception as e:
                logger.warning(f"Failed to reset page, discarding: {e}")
                try:
                    await page.close()
                except Exception:
                    pass
                async with self._lock:
                    self._pages_created -= 1
```

**A3. Make `/health` honest** so it can drive a watchdog. Add a public
`is_healthy` on the pool and return 503 when the browser is down:

```python
class BrowserPool:
    @property
    def is_healthy(self) -> bool:
        return self._browser is not None and self._browser.is_connected()

@app.get("/health")
async def health_check():
    if not browser_pool.is_healthy:
        raise HTTPException(status_code=503, detail="browser not connected")
    return {"status": "ok", "pool": browser_pool.stats}
```

> `is_connected()` catches a fully dead browser. If you want to also catch a
> browser that's connected but wedged, make `/health` optionally do a real
> probe (`acquire_page()` → `set_content("<html></html>")`) behind a
> `?deep=1` flag so routine polls stay cheap.

### Layer B — external watchdog (backstop, defense in depth)

Even with self-heal, add a systemd health probe so a truly wedged process gets
restarted. With `/health` now returning 503 when unhealthy, this is a
one-liner. Add a timer + oneshot:

`/etc/systemd/system/svan2d-playwright-health.service`
```ini
[Unit]
Description=Restart svan2d render server if unhealthy
[Service]
Type=oneshot
ExecStart=/usr/bin/curl -fsS -m 10 http://localhost:4000/health
ExecStopPost=/bin/sh -c '[ "$SERVICE_RESULT" = success ] || systemctl restart svan2d-playwright.service'
```

`/etc/systemd/system/svan2d-playwright-health.timer`
```ini
[Unit]
Description=Poll svan2d render server health
[Timer]
OnBootSec=2min
OnUnitActiveSec=2min
[Install]
WantedBy=timers.target
```
`systemctl enable --now svan2d-playwright-health.timer`

(Alternative: real systemd `WatchdogSec=` via `sd_notify`, but that needs the
app to ping the watchdog — more code than the probe above.)

### Optional — reduce the trigger (OOM)

The browser died under memory pressure before. Consider:
- `--disable-dev-shm-usage` is already set (good).
- Add `MemoryMax=` / `MemoryHigh=` to the unit so the browser is reaped and
  restarted predictably rather than taking the box down.
- Periodically recycle pages (e.g. close & recreate a page after N renders) to
  bound memory growth.

---

## Fix checklist
- [ ] A1 `_ensure_browser()` relaunch guard
- [ ] A2 `acquire_page()` validates/closes dead pages, calls `_ensure_browser()`
- [ ] A3 `/health` returns 503 when browser disconnected
- [ ] B  health timer + oneshot restart unit
- [ ] (opt) `MemoryHigh`/`MemoryMax` on the unit; per-page render cap
- [ ] Downstream (lunardelight, not svan2d): `ImageGenerator::processImageResult()`
      should treat a missing `png` key as failure instead of passing `null`
      down to the gateways.

## Verify after fixing
```bash
# healthy path
curl -fsS localhost:4000/health         # 200 {"status":"ok",...}
# simulate browser death, then confirm self-heal
pkill -f 'chrome.*--headless' ; sleep 1
curl -s -o /dev/null -w '%{http_code}\n' -X POST localhost:4000/render \
  -H 'Content-Type: application/json' \
  -d '{"type":"png","width":10,"height":10,"svg":"<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"10\" height=\"10\"><rect width=\"10\" height=\"10\"/></svg>"}'
# expect 200 (browser relaunched automatically), stats show pages_created>=1
curl -fsS localhost:4000/stats
```
