"""Ponto de entrada: python -m streamlit run app.py."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from alertagolpe.frontend import render_app

render_app(ROOT)
