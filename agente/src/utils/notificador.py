"""
Envio de alertas por e-mail quando há processos pendentes de aprovação.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import html
from typing import List, Dict, Any

from config import SMTP_HOST, SMTP_PORTA, SMTP_USUARIO, SMTP_SENHA, EMAIL_DESTINO
from utils.logger import info, erro


def enviar_alerta(processos: List[Dict[str, Any]]):
    """Envia e-mail com lista de processos aguardando aprovação."""
    if not all([SMTP_HOST, SMTP_USUARIO, SMTP_SENHA, EMAIL_DESTINO]):
        info("Configuração SMTP incompleta — alerta não enviado.")
        return

    if not processos:
        return

    assunto = f"[Custas TJDFT] {len(processos)} processo(s) aguardando aprovação"

    linhas = []
    for p in processos:
        numero_escapado = html.escape(str(p.get('numero', '')))
        status_escapado = html.escape(str(p.get('status', '')))
        linhas.append(f"<li>{numero_escapado} — {status_escapado}</li>")

    corpo = f"""
    <html>
    <body>
        <p>Olá,</p>
        <p>Os seguintes processos estão aguardando aprovação no dashboard:</p>
        <ul>
            {''.join(linhas)}
        </ul>
        <p>Acesse o dashboard para revisar e aprovar.</p>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"] = SMTP_USUARIO
    msg["To"] = EMAIL_DESTINO
    msg.attach(MIMEText(corpo, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORTA, timeout=30) as server:
            server.starttls()
            server.login(SMTP_USUARIO, SMTP_SENHA)
            server.sendmail(SMTP_USUARIO, EMAIL_DESTINO, msg.as_string())
        info("E-mail de alerta enviado com sucesso.")
    except Exception as e:
        erro(f"Falha ao enviar e-mail: {e}")
