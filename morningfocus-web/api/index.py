"""Vercel entry point — re-exports the FastAPI app."""
import sys
from pathlib import Path

# Ensure `morningfocus-web/` is on the path so `app.*` imports resolve
# whether Vercel runs this file from the repo root or the subfolder.
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app  # noqa: E402, F401
