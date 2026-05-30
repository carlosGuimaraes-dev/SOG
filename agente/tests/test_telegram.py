import pytest
import requests

from config import validar_requisitos_homologacao_local
from utils import telegram


class FakeResponse:
    def __init__(self, status_code=200):
        self.status_code = status_code


def test_sender_usa_send_message_notify_only():
    chamadas = []

    def fake_post(url, json, timeout):
        chamadas.append((url, json, timeout))
        return FakeResponse()

    enviado = telegram.enviar_mensagem(
        "mensagem operacional",
        http_post=fake_post,
        token="token-test",
        chat_id="chat-test",
    )

    assert enviado is True
    url, payload, timeout = chamadas[0]
    assert url == "https://api.telegram.org/bottoken-test/sendMessage"
    assert payload == {
        "chat_id": "chat-test",
        "text": "mensagem operacional",
        "disable_web_page_preview": True,
    }
    assert timeout == 10


def test_falha_http_nao_propaga_excecao():
    def fake_post(_url, **_kwargs):
        raise requests.Timeout("timeout")

    assert telegram.enviar_mensagem(
        "mensagem",
        http_post=fake_post,
        token="token-test",
        chat_id="chat-test",
    ) is False


def test_resumo_lote_usa_apenas_dados_agregados():
    chamadas = []
    membros = [
        {
            "numero": "0701234-56.2024.8.07.0001",
            "parte": "Maria da Silva",
            "documento": "sentença sigilosa",
            "status_atual": "emitido",
        },
        {
            "numero": "0711111-22.2024.8.07.0001",
            "parte": "João Souza",
            "documento": "laudo",
            "status_atual": "erro",
        },
    ]

    def fake_post(_url, **kwargs):
        chamadas.append(kwargs["json"])
        return FakeResponse()

    telegram.notificar_ciclo_concluido(
        {"criado_em": "2026-05-29 10:00:00", "finalizado_em": "2026-05-29 10:03:05"},
        membros,
        http_post=fake_post,
        token="token-test",
        chat_id="chat-test",
    )

    texto = chamadas[0]["text"]
    assert "Total: 2" in texto
    assert "erro: 1" in texto
    assert "emitido: 1" in texto
    assert "Tempo total: 00:03:05" in texto
    assert "dashboard" in texto
    assert "0701234" not in texto
    assert "0711111" not in texto
    assert "Maria" not in texto
    assert "João" not in texto
    assert "sentença" not in texto
    assert "laudo" not in texto


def test_validacao_homologacao_exige_telegram_sem_exigir_smtp(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token-test")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "chat-test")
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.delenv("SMTP_USUARIO", raising=False)
    monkeypatch.delenv("SMTP_SENHA", raising=False)
    monkeypatch.delenv("EMAIL_DESTINO", raising=False)

    validar_requisitos_homologacao_local()


def test_validacao_homologacao_falha_sem_telegram(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    with pytest.raises(RuntimeError) as exc_info:
        validar_requisitos_homologacao_local()

    assert "TELEGRAM_BOT_TOKEN" in str(exc_info.value)
    assert "TELEGRAM_CHAT_ID" in str(exc_info.value)
