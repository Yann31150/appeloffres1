"""Configuration et constantes de l'application."""

from pathlib import Path

# Répertoire de sortie
OUTPUT_ROOT = Path.cwd() / "output"
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)


