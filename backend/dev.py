"""Dev server: `uv run dev.py` desde backend/ (uvicorn con reload en 127.0.0.1:8000).

Nota: `uv run dev` (nombre pelado) no es soportado por uv — uv no tiene
alias de tareas como npm; solo resuelve ejecutables o rutas a scripts.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from main import run

if __name__ == "__main__":
    # Uso: uv run dev.py [--log-level debug] desde backend/
    # (uvicorn main:app directo falla: main vive en src/, no en backend/).
    log_level = "info"
    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--log-level" and i + 1 < len(sys.argv[1:]):
            log_level = sys.argv[1:][i + 1]
        elif arg.startswith("--log-level="):
            log_level = arg.split("=", 1)[1]
    run(log_level=log_level)
