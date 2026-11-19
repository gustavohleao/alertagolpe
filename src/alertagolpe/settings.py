"""Configuração lida a cada execução, sem alterar o ambiente do processo."""

from __future__ import annotations

from collections.abc import Mapping
import os
from pathlib import Path

from dotenv import dotenv_values


_DEFAULTS = {
    "LLM_PROVIDER": "gemini",
    "GEMINI_API_KEY": "",
    "LLM_MODEL": "",
    # Modelos tentados, em ordem, se o principal estiver sobrecarregado ou indisponível.
    "LLM_FALLBACK_MODELS": "gemini-3.1-flash-lite,gemini-flash-lite-latest",
    "OLLAMA_BASE_URL": "http://localhost:11434",
    "OLLAMA_MODEL": "",
    "LLM_TIMEOUT_SECONDS": "90",
}


def load_settings(root: Path, *, environ: Mapping[str, str] | None = None) -> dict[str, str]:
    """Combina padrões, arquivo local e variáveis explícitas, nessa ordem.

    Uma variável do processo prevalece mesmo quando seu valor é vazio. Valores
    literais como ``${NOME}`` não são expandidos. Apenas as opções conhecidas
    são retornadas; o conteúdo e os segredos não são registrados em logs.
    """
    file_values = dotenv_values(Path(root) / ".env", interpolate=False)
    process_values = os.environ if environ is None else environ
    settings = dict(_DEFAULTS)
    for name in _DEFAULTS:
        if name in file_values:
            value = file_values[name]
            settings[name] = "" if value is None else value
        if name in process_values:
            value = process_values[name]
            settings[name] = "" if value is None else value
    # gemini (padrão, nuvem) ou ollama (modelo local). Outro valor volta ao padrão.
    provider = settings["LLM_PROVIDER"].strip().lower()
    settings["LLM_PROVIDER"] = provider if provider in ("gemini", "ollama") else "gemini"
    return settings

