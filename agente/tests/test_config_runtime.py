from pathlib import Path

import config


def test_init_config_prefere_env_agente_ao_env_legado(monkeypatch, tmp_path):
    env_agente = tmp_path / ".env.agente"
    env_legado = tmp_path / ".env"
    db_path = tmp_path / "dados" / "custas.db"

    env_agente.write_text(f"DB_PATH={db_path}\n", encoding="utf-8")
    env_legado.write_text("DB_PATH=/tmp/nao-usar.db\n", encoding="utf-8")

    monkeypatch.setattr(config, "PROJECT_ROOT", tmp_path)
    monkeypatch.delenv("DB_PATH", raising=False)

    config.init_config()

    assert config.DB_PATH == str(db_path)
    assert Path(config.DB_PATH).parent.exists()
