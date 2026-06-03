import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from banco import db
from sog_shared.infra_db import SCHEMA_PATH


def test_agente_reusa_schema_compartilhado_canonico():
    assert db.SCHEMA_PATH == SCHEMA_PATH
