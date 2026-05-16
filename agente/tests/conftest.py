import sys
from pathlib import Path

# Adiciona agente/src ao path para imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
# Adiciona shared/ ao path para importar sog_shared sem instalação
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))
