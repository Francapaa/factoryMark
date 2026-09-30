"""Dev server: `uv run dev.py` desde backend/ (uvicorn con reload en 127.0.0.1:8000).

Nota: `uv run dev` (nombre pelado) no es soportado por uv — uv no tiene
alias de tareas como npm; solo resuelve ejecutables o rutas a scripts.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from main import run

if __name__ == "__main__":
    run()
