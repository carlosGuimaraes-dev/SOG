"""
Facade de compatibilidade para o pacote compartilhado.

O código de domínio foi separado em módulos por fronteira:
  - processos_aprovacao
  - agente_ciclos
  - tarefas_sessoes
  - infra_db
"""

from sog_shared.agente_ciclos import *  # noqa: F401,F403
from sog_shared.infra_db import *  # noqa: F401,F403
from sog_shared.processos_aprovacao import *  # noqa: F401,F403
from sog_shared.tarefas_sessoes import *  # noqa: F401,F403

ETAPA_EVIDENCIA_DEMONSTRATIVO_SISTJ = "demonstrativo_emitido_sistj"
ETAPA_EVIDENCIA_ANEXO_PJE = "demonstrativo_anexado_pje"
