import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"

# Add both root (for config/, src/) and backend/ (for app/) to sys.path
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(BACKEND))

os.chdir(BACKEND)

import uvicorn  # noqa: E402

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(BACKEND), str(ROOT / "src"), str(ROOT / "config")],
    )
