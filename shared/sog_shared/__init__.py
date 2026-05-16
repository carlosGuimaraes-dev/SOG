"""
Pacote compartilhado SOG (Sistema de Ordem de Guias).

Contém:
  - db: acesso ao banco SQLite (schema, conexão, operações CRUD)
  - schemas: models Pydantic para validação e serialização
  - config: variáveis de ambiente comuns (sem side-effects no import)
"""
