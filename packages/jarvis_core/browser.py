from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from playwright.async_api import Browser, Page, async_playwright


@dataclass(frozen=True)
class BrowserEvidence:
    url: str
    title: str
    screenshot_path: str


class BrowserService:
    """Headless Playwright browser service for VPS-safe web tasks."""

    def __init__(self, headless: bool = True, executable_path: str | None = None):
        self.headless = headless
        self.executable_path = executable_path
        self._playwright = None
        self._browser: Browser | None = None

    async def start(self) -> None:
        if self._browser:
            return
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            executable_path=self.executable_path or None,
        )

    async def stop(self) -> None:
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def screenshot(self, url: str, output_path: str, full_page: bool = True) -> BrowserEvidence:
        await self.start()
        assert self._browser is not None
        page: Page = await self._browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            title = await page.title()
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=output_path, full_page=full_page)
            return BrowserEvidence(url=url, title=title, screenshot_path=output_path)
        finally:
            await page.close()
