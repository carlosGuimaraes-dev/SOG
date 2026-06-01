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
        return

    sync_api = types.ModuleType("playwright.sync_api")

    class _PlaywrightTimeout(Exception):
        pass

    def _sync_playwright():
        raise RuntimeError("playwright indisponível neste ambiente de teste")

    sync_api.sync_playwright = _sync_playwright
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
