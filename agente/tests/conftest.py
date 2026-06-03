import importlib.util
import sys
from pathlib import Path
import types

# Adiciona agente/src ao path para imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
# Adiciona shared/ ao path para importar sog_shared sem instalação
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))


def _instalar_stub_playwright() -> None:
    if importlib.util.find_spec("playwright") is not None:
        try:
            import playwright.sync_api  # noqa: F401
            return
        except Exception:
            pass

    sync_api = types.ModuleType("playwright.sync_api")

    class _PlaywrightTimeout(Exception):
        pass

    class _DummyPlaywrightRunner:
        def start(self):
            raise RuntimeError("playwright indisponivel neste ambiente de teste")

    sync_api.sync_playwright = lambda: _DummyPlaywrightRunner()
    sync_api.Page = object
    sync_api.Browser = object
    sync_api.BrowserContext = object
    sync_api.FrameLocator = object
    sync_api.TimeoutError = _PlaywrightTimeout

    playwright = types.ModuleType("playwright")
    playwright.sync_api = sync_api

    sys.modules.setdefault("playwright", playwright)
    sys.modules.setdefault("playwright.sync_api", sync_api)


_instalar_stub_playwright()
