"""v14_spark_root_001 — één bron voor de project-root. Op Emergent is dat /app, op de Odroid de map waar je
de repo uitpakte. Override met env SPARK_ROOT; anders afgeleid van dit bestand (backend/modules/core/paths.py)."""
import os
from pathlib import Path

SPARK_ROOT = Path(os.environ.get("SPARK_ROOT") or Path(__file__).resolve().parents[3])
BACKEND_DIR = SPARK_ROOT / "backend"
DATA_DIR = Path(os.environ.get("SPARK_DATA_DIR") or BACKEND_DIR / "data")
MEMORY_DIR = SPARK_ROOT / "memory"
