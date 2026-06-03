"""
Pacote compartilhado SOG (Sistema de Ordem de Guias).

Contém:
  - infra_db: schema, conexão e bootstrap do SQLite compartilhado
  - processos_aprovacao: operações de domínio para processos e aprovação
  - agente_ciclos: operações de domínio para controle do agente e ciclos
  - tarefas_sessoes: operações de domínio para tarefas e sessões externas
  - db: facade de compatibilidade sobre os módulos acima
  - schemas: models Pydantic para validação e serialização
  - config: variáveis de ambiente comuns (sem side-effects no import)
"""
