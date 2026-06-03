import sys
import types


def _instalar_stub_playwright() -> None:
    if "playwright.sync_api" in sys.modules:
        return

    sync_api = types.ModuleType("playwright.sync_api")

    class _DummyTimeoutError(Exception):
        pass

    class _DummyPage:
        pass

    class _DummyBrowser:
        pass

    class _DummyBrowserContext:
        pass

    class _DummyFrameLocator:
        pass

    class _DummyPlaywrightRunner:
        def start(self):
            raise RuntimeError("playwright nao disponivel neste ambiente de teste")

    sync_api.TimeoutError = _DummyTimeoutError
    sync_api.Page = _DummyPage
    sync_api.Browser = _DummyBrowser
    sync_api.BrowserContext = _DummyBrowserContext
    sync_api.FrameLocator = _DummyFrameLocator
    sync_api.sync_playwright = lambda: _DummyPlaywrightRunner()

    playwright = types.ModuleType("playwright")
    playwright.sync_api = sync_api

    sys.modules["playwright"] = playwright
    sys.modules["playwright.sync_api"] = sync_api


_instalar_stub_playwright()
