"""Loaded from the PythonAnywhere Web tab's WSGI file (see DEPLOYMENT.md)."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from setup_hosting import configure

configure()
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
