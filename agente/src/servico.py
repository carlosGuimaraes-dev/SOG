"""
Serviço longo do agente de custas processuais TJDFT.

Implementa máquina de estados com loop infinito, graceful shutdown
via signals (SIGINT/SIGTERM) e comunicação bidirecional com o
dashboard via tabela SQLite `agente_controle`.

Estados:
    parado → iniciando → autenticando → executando → dormindo → executando → ...
                                              ↓
                                      parando → interrompido
                                      aguardando_login → executando

Uso:
    python agente/src/servico.py
"""
import os
import signal
import sys
import threading
from pathlib import Path
from typing import Tuple

# Garante que o pacote shared/ está acessível quando rodando no host
SHARED_DIR = Path(__file__).resolve().parent.parent.parent / "shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from config import init_config
from modulos.pje import PjeClient
from modulos.sistjweb import SistjClient
from modulos.emissor import emitir_pendentes
from modulos.executor_tarefas import executar_tarefa
from modulos.auth_manager import ReautenticacaoNecessariaError
from pipeline import rodar_pipeline
from sog_shared.db import (
    init_db,
    obter_controle_agente,
    criar_ou_atualizar_controle_agente,
    pausar_ciclo_agente,
    proxima_tarefa_pendente,
    concluir_tarefa,
    devolver_tarefa_pendente,
)
from utils.logger import info, erro, aviso

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

ESTADOS_VALIDOS = frozenset({
    "parado",
    "iniciando",
    "autenticando",
    "executando",
    "dormindo",
    "aguardando_login",
    "erro",
    "erro_pausado",
    "parando",
    "pausado",
    "interrompido",
})

TEMPO_DORMIR_SEGUNDOS = 30
TEMPO_ERRO_SEGUNDOS = 30
TEMPO_ESPERA_CURTA_SEGUNDOS = 5


class AgenteServico:
    """Serviço longo com máquina de estados e graceful shutdown."""

    def __init__(self):
        self._stop_event = threading.Event()
        self.pje = PjeClient()
        self.sistj = SistjClient()
        self._status_atual = "parado"
        self._mensagem_atual = ""
        self._locks = {"pje": False, "sistj": False}
        self._tarefas_por_iteracao = 3

    # ------------------------------------------------------------------
    # Ciclo de vida público
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Entry point do serviço longo."""
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        init_config()
        init_db()

        # Garante registro de controle e registra PID
        self._set_status("parado", "Serviço iniciado. Aguardando comando.")
        self._atualizar_pid()

        info(f"AgenteServico iniciado. PID={os.getpid()}. Aguardando comando...")

        while not self._stop_event.is_set():
            try:
                self._loop_iteration()
            except Exception as e:
                erro(f"Erro não tratado no loop principal: {e}")
                self._set_status("erro", str(e))
                self._stop_event.wait(timeout=TEMPO_ERRO_SEGUNDOS)

        self._cleanup()
        self._set_status("parado", "Serviço encerrado.")
        info("AgenteServico finalizado.")

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    def _handle_signal(self, signum: int, _frame) -> None:
        self._stop_event.set()
        self._set_status("parando", f"Sinal {signum} recebido. Finalizando...")
        aviso(f"Signal {signum} capturado. Iniciando graceful shutdown...")

    # ------------------------------------------------------------------
    # Loop principal — máquina de estados
    # ------------------------------------------------------------------

    def _loop_iteration(self) -> None:
        """Uma iteração da máquina de estados."""
        # Sempre atualiza heartbeat para dashboard detectar online
        self._atualizar_heartbeat()

        comando, status_db = self._ler_comando()

        # Stop externo do processo encerra; comando do dashboard pausa o ciclo.
        if self._stop_event.is_set():
            if status_db != "parando":
                self._set_status("parando", "Encerramento do processo recebido.")
            return
        if comando == "parar" and status_db in {
            "iniciando",
            "autenticando",
            "executando",
            "dormindo",
            "parando",
        }:
            self._pausar_ciclo("interrompido", "Ciclo pausado por solicitação do dashboard.")
            return

        # Estado inicial/retomado + comando iniciar → autenticar
        if status_db in {"parado", "pausado", "interrompido", "iniciando"} and comando == "iniciar":
            self._set_status("autenticando", "Iniciando autenticação...")
            return

        # Estado autenticando → tenta login nos dois sistemas
        if status_db == "autenticando":
            try:
                self._autenticar_todos()
                self._set_status("executando", "Autenticação OK. Iniciando execução.")
            except ReautenticacaoNecessariaError as e:
                self._pausar_ciclo(
                    "aguardando_login",
                    f"Sessão {e.sistema} expirada. Faça login no navegador.",
                )
            except Exception as e:
                erro(f"Falha na autenticação: {e}")
                self._pausar_ciclo("erro_pausado", f"Falha na autenticação: {e}")
            return

        # Estado aguardando_login → dispara fallback interativo
        if status_db == "aguardando_login":
            if comando != "iniciar":
                self._stop_event.wait(timeout=TEMPO_ESPERA_CURTA_SEGUNDOS)
                return
            try:
                self._autenticar_interativo()
                self._set_status("executando", "Reautenticação OK. Retomando execução.")
            except TimeoutError:
                self._pausar_ciclo("erro_pausado", "Timeout aguardando login manual.")
            except Exception as e:
                erro(f"Falha na reautenticação interativa: {e}")
                self._pausar_ciclo("erro_pausado", f"Falha na reautenticação: {e}")
            return

        # Estado executando → processa tarefas pendentes primeiro, depois pipeline
        if status_db == "executando":
            try:
                tarefas_processadas = self._processar_tarefas_pendentes(
                    max_tarefas=self._tarefas_por_iteracao
                )
                if self._status_atual == "aguardando_login":
                    return
                if self._deve_pausar_por_comando():
                    self._pausar_ciclo("interrompido", "Ciclo pausado após tarefa segura.")
                    return
                if tarefas_processadas > 0 and self._ha_mais_tarefas_pendentes():
                    return  # volta ao loop sem dormir para processar mais tarefas

                self._processar_iteracao()
                if self._deve_pausar_por_comando():
                    self._pausar_ciclo("interrompido", "Ciclo pausado após etapa segura.")
                    return
                self._set_status("dormindo", "Iteração concluída. Aguardando próximo ciclo.")
            except ReautenticacaoNecessariaError as e:
                self._pausar_ciclo(
                    "aguardando_login",
                    f"Sessão {e.sistema} expirada durante execução.",
                )
            except Exception as e:
                erro(f"Erro durante execução: {e}")
                self._pausar_ciclo("erro_pausado", str(e))
            return

        # Estado dormindo → aguarda 30s interrompível
        if status_db == "dormindo":
            if self._aguardar_ou_pausar(TEMPO_DORMIR_SEGUNDOS):
                return
            if not self._stop_event.is_set():
                self._set_status("executando", "Retomando execução.")
            return

        # Estado erro → aguarda 30s e tenta recuperar
        if status_db == "erro":
            self._stop_event.wait(timeout=TEMPO_ERRO_SEGUNDOS)
            if not self._stop_event.is_set():
                self._set_status("executando", "Tentando recuperação após erro.")
            return

        # Estado parando → pausa cooperativa no ciclo atual
        if status_db == "parando":
            self._pausar_ciclo("interrompido", "Ciclo pausado.")
            return

        if status_db in {"pausado", "interrompido", "erro_pausado"}:
            self._stop_event.wait(timeout=TEMPO_ESPERA_CURTA_SEGUNDOS)
            return

        # Estado desconhecido — espera curta
        aviso(f"Estado desconhecido no banco: {status_db}")
        self._stop_event.wait(timeout=TEMPO_ESPERA_CURTA_SEGUNDOS)

    # ------------------------------------------------------------------
    # Ações por estado
    # ------------------------------------------------------------------

    def _autenticar_todos(self) -> None:
        """Autentica PJe e SISTJWEB usando AuthManager (storage state + fallback interativo)."""
        info("Autenticando no PJE...")
        self.pje.garantir_autenticado()

        info("Autenticando no SISTJWEB...")
        self.sistj.garantir_autenticado()

        info("Autenticação concluída em ambos os sistemas.")

    def _autenticar_interativo(self) -> bool:
        """Chamado quando status='aguardando_login'. Abre navegador visível se necessário."""
        info("Tentando reautenticação interativa no PJE...")
        self.pje.garantir_autenticado()

        info("Tentando reautenticação interativa no SISTJWEB...")
        self.sistj.garantir_autenticado()

        info("Reautenticação interativa concluída.")
        return True

    def _processar_tarefas_pendentes(self, max_tarefas: int = 3) -> int:
        """Processa até N tarefas pendentes. Retorna quantas processou."""
        processadas = 0
        for _ in range(max_tarefas):
            if self._deve_pausar_por_comando():
                break

            tarefa = proxima_tarefa_pendente()
            if not tarefa:
                break

            sistema = tarefa.get("sistema_alvo", "ambos")
            sistemas = [sistema] if sistema != "ambos" else ["pje", "sistj"]

            # Verifica lock
            if any(self._locks[s] for s in sistemas):
                # Devolve à fila como pendente sem marcar conclusão
                devolver_tarefa_pendente(tarefa["id"])
                aviso(f"Tarefa {tarefa['id']} adiada — sistema {sistema} ocupado.")
                continue

            # Adquire lock
            for s in sistemas:
                self._locks[s] = True

            try:
                info(f"Executando tarefa {tarefa['id']}: {tarefa['tipo']}")
                resultado = executar_tarefa(tarefa, self.pje, self.sistj)
                concluida = concluir_tarefa(tarefa["id"], "concluido", resultado=resultado)
                if concluida:
                    info(f"Tarefa {tarefa['id']} concluída.")
                else:
                    aviso(f"Tarefa {tarefa['id']} foi cancelada durante a execução.")
            except ReautenticacaoNecessariaError as e:
                devolver_tarefa_pendente(tarefa["id"])
                self._pausar_ciclo("aguardando_login", f"Sessão {e.sistema} expirada durante tarefa.")
                processadas += 1
                break
            except Exception as e:
                erro(f"Erro na tarefa {tarefa['id']}: {e}")
                concluir_tarefa(tarefa["id"], "erro", mensagem_erro=str(e))
            finally:
                for s in sistemas:
                    self._locks[s] = False

            processadas += 1

        return processadas

    def _ha_mais_tarefas_pendentes(self) -> bool:
        from sog_shared.db import get_conn

        with get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM agente_tarefas WHERE status = 'pendente'"
            ).fetchone()
            return (row[0] if row else 0) > 0

    def _processar_iteracao(self) -> None:
        """Coleta, preenche e emite em um ciclo."""
        # Pipeline: coleta e preenche novos processos
        if self._deve_pausar_por_comando():
            return
        rodar_pipeline(self.pje, self.sistj)

        # Emissão: processa aprovados
        if self._deve_pausar_por_comando():
            return
        emitir_pendentes(self.sistj, self.pje)

    # ------------------------------------------------------------------
    # Comunicação com SQLite (agente_controle)
    # ------------------------------------------------------------------

    def _ler_comando(self) -> Tuple[str, str]:
        """Lê comando e status atual do SQLite. Retorna (comando, status)."""
        controle = obter_controle_agente()
        if not controle:
            return "parar", "parado"
        return (
            controle.get("comando", "parar"),
            controle.get("status", "parado"),
        )

    def _set_status(self, status: str, mensagem: str = "") -> None:
        """Atualiza status do agente no SQLite."""
        if status not in ESTADOS_VALIDOS:
            aviso(f"Status inválido: {status}. Usando 'erro'.")
            status = "erro"
        self._status_atual = status
        self._mensagem_atual = mensagem
        try:
            criar_ou_atualizar_controle_agente(status=status, mensagem=mensagem)
        except Exception as e:
            erro(f"Falha ao persistir status no banco: {e}")

    def _pausar_ciclo(self, status: str, mensagem: str) -> None:
        """Pausa o ciclo preservando UUID/snapshot para retomada."""
        if status not in ESTADOS_VALIDOS:
            status = "erro_pausado"
        self._status_atual = status
        self._mensagem_atual = mensagem
        try:
            pausar_ciclo_agente(status=status, mensagem=mensagem)
        except Exception as e:
            erro(f"Falha ao persistir pausa no banco: {e}")

    def _deve_pausar_por_comando(self) -> bool:
        comando, _status_db = self._ler_comando()
        return comando == "parar" or self._stop_event.is_set()

    def _aguardar_ou_pausar(self, segundos: int) -> bool:
        for _ in range(segundos):
            if self._deve_pausar_por_comando():
                self._pausar_ciclo("interrompido", "Ciclo pausado durante espera.")
                return True
            if self._stop_event.wait(timeout=1):
                return True
        return False

    def _atualizar_heartbeat(self) -> None:
        """Atualiza timestamp e PID no banco (para dashboard detectar online)."""
        try:
            criar_ou_atualizar_controle_agente(
                pid=os.getpid(),
            )
        except Exception as e:
            # Não falha o loop por problema de heartbeat
            aviso(f"Falha ao atualizar heartbeat: {e}")

    def _atualizar_pid(self) -> None:
        """Registra o PID do processo no banco."""
        try:
            criar_ou_atualizar_controle_agente(pid=os.getpid())
        except Exception as e:
            aviso(f"Falha ao registrar PID: {e}")

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def _cleanup(self) -> None:
        """Fecha browsers e libera recursos."""
        info("Executando cleanup: fechando browsers...")
        try:
            self.pje.fechar()
        except Exception as e:
            aviso(f"Erro ao fechar PJeClient: {e}")
        try:
            self.sistj.fechar()
        except Exception as e:
            aviso(f"Erro ao fechar SistjClient: {e}")


if __name__ == "__main__":
    AgenteServico().run()
