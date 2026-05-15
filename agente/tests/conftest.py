import sys
from pathlib import Path

# Adiciona agente/src ao path para imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
