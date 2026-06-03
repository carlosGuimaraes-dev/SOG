from pathlib import Path
from unittest.mock import MagicMock
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from modulos.auth_manager import AuthManager
from modulos.session_profile import SessionProfile


def test_session_profile_reusa_profile_persistente(tmp_path):
    chromium = MagicMock()
    profile = SessionProfile(tmp_path / "pje-state.json")

    profile.launch_persistent_context(chromium, headless=True, accept_downloads=True)

    chromium.launch_persistent_context.assert_called_once_with(
        user_data_dir=str(profile.profile_dir),
        headless=True,
        viewport={"width": 1920, "height": 1080},
        accept_downloads=True,
    )


def test_session_profile_persiste_snapshot_compativel(tmp_path):
    context = MagicMock()
    profile = SessionProfile(tmp_path / "pje-state.json")

    profile.persist_storage_state(context)

    context.storage_state.assert_called_once_with(path=str(profile.storage_path))


def test_iniciar_usa_profile_persistente_como_caminho_principal(tmp_path, monkeypatch):
    page = MagicMock()
    context = MagicMock()
    context.browser = MagicMock()
    context.pages = []
    context.new_page.return_value = page

    chromium = MagicMock()
    chromium.launch_persistent_context.return_value = context

    runner = MagicMock()
    runner.chromium = chromium
    runner.start.return_value = runner

    monkeypatch.setattr("modulos.auth_manager.sync_playwright", lambda: runner)

    auth = AuthManager(tmp_path / "pje-state.json")
    auth.iniciar(accept_downloads=True)

    chromium.launch_persistent_context.assert_called_once_with(
        user_data_dir=str(auth.profile_dir),
        headless=True,
        viewport={"width": 1920, "height": 1080},
        accept_downloads=True,
    )
    context.new_page.assert_called_once_with()
    assert auth.page is page


def test_iniciar_reusa_primeira_aba_do_profile_existente(tmp_path, monkeypatch):
    page = MagicMock()
    context = MagicMock()
    context.browser = MagicMock()
    context.pages = [page]

    chromium = MagicMock()
    chromium.launch_persistent_context.return_value = context

    runner = MagicMock()
    runner.chromium = chromium
    runner.start.return_value = runner

    monkeypatch.setattr("modulos.auth_manager.sync_playwright", lambda: runner)

    auth = AuthManager(tmp_path / "pje-state.json")
    auth.iniciar()

    context.new_page.assert_not_called()
    assert auth.page is page


def test_forcar_reautenticacao_interativa_mantem_navegador_visivel():
    auth = AuthManager(Path("/tmp/sistj-state.json"))
    auth.page = MagicMock()
    auth.fechar = MagicMock()
    auth.iniciar = MagicMock()
    auth._fallback_interativo = MagicMock()

    verificar = MagicMock(return_value=True)

    resultado = auth.forcar_reautenticacao_interativa(
        url="https://sistj.example",
        verificar_sucesso_fn=verificar,
        manter_aberto_apos_login=True,
    )

    assert resultado is True
    auth.fechar.assert_called_once()
    auth._fallback_interativo.assert_called_once_with(
        "https://sistj.example",
        verificar,
        600_000,
        accept_downloads=False,
        manter_aberto_apos_login=True,
    )
    auth.iniciar.assert_not_called()
    auth.page.goto.assert_not_called()
    auth.page.wait_for_timeout.assert_not_called()
    verificar.assert_called_once_with(auth.page)


def test_fallback_interativo_usa_contexto_persistente(tmp_path, monkeypatch):
    page = MagicMock()
    page.url = "https://pje.example"

    context = MagicMock()
    context.browser = MagicMock()
    context.pages = [page]

    chromium = MagicMock()
    chromium.launch_persistent_context.return_value = context

    runner = MagicMock()
    runner.chromium = chromium
    runner.start.return_value = runner

    monkeypatch.setattr("modulos.auth_manager.sync_playwright", lambda: runner)

    auth = AuthManager(tmp_path / "pje-state.json")
    verificar = MagicMock(return_value=True)

    auth._fallback_interativo(
        "https://pje.example",
        verificar,
        10_000,
        accept_downloads=True,
        manter_aberto_apos_login=True,
    )

    chromium.launch_persistent_context.assert_called_once_with(
        user_data_dir=str(auth.profile_dir),
        headless=False,
        viewport={"width": 1920, "height": 1080},
        accept_downloads=True,
    )
    context.storage_state.assert_called_once_with(path=str(auth.storage_path))
    assert auth.page is page
    assert auth.context is context


def test_sistj_reautenticacao_interativa_mantem_sessao_aberta():
    from modulos.sistjweb import SistjClient

    cliente = SistjClient()
    cliente._auth.forcar_reautenticacao_interativa = MagicMock(return_value=True)

    resultado = cliente.reautenticar_interativo()

    assert resultado is True
    cliente._auth.forcar_reautenticacao_interativa.assert_called_once()
    _, kwargs = cliente._auth.forcar_reautenticacao_interativa.call_args
    assert kwargs["manter_aberto_apos_login"] is True


def test_pje_reautenticacao_interativa_mantem_sessao_aberta():
    from modulos.pje import PjeClient

    cliente = PjeClient()
    cliente._auth.forcar_reautenticacao_interativa = MagicMock(return_value=True)

    resultado = cliente.reautenticar_interativo()

    assert resultado is True
    cliente._auth.forcar_reautenticacao_interativa.assert_called_once()
    _, kwargs = cliente._auth.forcar_reautenticacao_interativa.call_args
    assert kwargs["accept_downloads"] is True
    assert kwargs["manter_aberto_apos_login"] is True
