import sys
from pathlib import Path

# Adiciona api/src e agente/src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agente" / "src"))
