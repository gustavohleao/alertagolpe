"""Configuração com arquivos fictícios; não lê o .env real do projeto."""

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from estudapdf.settings import load_settings


class SettingsTests(unittest.TestCase):
    def setUp(self):
        temp_root = Path(__file__).resolve().parents[1] / ".tools" / "test-temp"
        temp_root.mkdir(parents=True, exist_ok=True)
        directory = tempfile.TemporaryDirectory(prefix="settings-", dir=temp_root)
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def write_env(self, text):
        (self.root / ".env").write_text(text, encoding="utf-8")

    def test_missing_file_returns_all_defaults(self):
        self.assertEqual(
            load_settings(self.root, environ={}),
            {
                "LLM_PROVIDER": "gemini",
                "GEMINI_API_KEY": "",
                "LLM_MODEL": "",
                "OLLAMA_BASE_URL": "http://localhost:11434",
                "OLLAMA_MODEL": "",
                "LLM_TIMEOUT_SECONDS": "90",
            },
        )

    def test_rewriting_file_updates_key_on_next_load_without_restart(self):
        self.write_env("GEMINI_API_KEY=chave-ficticia-a\nLLM_MODEL=modelo-a\n")
        first = load_settings(self.root, environ={})
        self.write_env("GEMINI_API_KEY=chave-ficticia-b\nLLM_MODEL=modelo-b\n")
        second = load_settings(self.root, environ={})
        self.assertEqual(first["GEMINI_API_KEY"], "chave-ficticia-a")
        self.assertEqual(second["GEMINI_API_KEY"], "chave-ficticia-b")
        self.assertEqual(second["LLM_MODEL"], "modelo-b")

    def test_explicit_environment_precedes_file_including_intentional_empty(self):
        self.write_env("LLM_PROVIDER=ollama\nGEMINI_API_KEY=chave-do-arquivo\nLLM_MODEL=modelo-do-arquivo\n")
        settings = load_settings(
            self.root,
            environ={"LLM_PROVIDER": "gemini", "GEMINI_API_KEY": "", "LLM_MODEL": "modelo-do-processo"},
        )
        self.assertEqual(settings["LLM_PROVIDER"], "gemini")
        self.assertEqual(settings["GEMINI_API_KEY"], "")
        self.assertEqual(settings["LLM_MODEL"], "modelo-do-processo")

    def test_default_environ_reads_process_variables(self):
        self.write_env("GEMINI_API_KEY=chave-ficticia-arquivo\n")
        with patch.dict(os.environ, {"GEMINI_API_KEY": "chave-ficticia-processo"}):
            settings = load_settings(self.root)
            self.assertEqual(settings["GEMINI_API_KEY"], "chave-ficticia-processo")

    def test_loading_file_mutates_neither_mapping_nor_process(self):
        self.write_env("GEMINI_API_KEY=chave-ficticia-arquivo\nLLM_MODEL=modelo-ficticio\n")
        explicit = {"LLM_PROVIDER": "ollama"}
        original_mapping = dict(explicit)
        with patch.dict(os.environ, {"GEMINI_API_KEY": "sentinela-ficticia"}):
            os.environ.pop("LLM_MODEL", None)
            settings = load_settings(self.root, environ=explicit)
            self.assertEqual(settings["GEMINI_API_KEY"], "chave-ficticia-arquivo")
            self.assertEqual(os.environ["GEMINI_API_KEY"], "sentinela-ficticia")
            self.assertNotIn("LLM_MODEL", os.environ)
        self.assertEqual(explicit, original_mapping)

    def test_sensitive_interpolation_syntax_stays_literal(self):
        self.write_env("GEMINI_API_KEY='literal-${EXTERNAL_SECRET}'\nLLM_MODEL=${MODEL_NAME}\n")
        settings = load_settings(self.root, environ={"EXTERNAL_SECRET": "nao-expandir", "MODEL_NAME": "nao-expandir"})
        self.assertEqual(settings["GEMINI_API_KEY"], "literal-${EXTERNAL_SECRET}")
        self.assertEqual(settings["LLM_MODEL"], "${MODEL_NAME}")
        self.assertNotIn("EXTERNAL_SECRET", settings)
        self.assertNotIn("MODEL_NAME", settings)

    def test_bare_values_map_to_empty_strings_and_unknown_options_are_ignored(self):
        self.write_env("GEMINI_API_KEY\nLLM_MODEL\nUNKNOWN_SETTING=nao-retornar\n")
        settings = load_settings(self.root, environ={"ANOTHER_UNKNOWN": "nao-retornar"})
        self.assertEqual(settings["GEMINI_API_KEY"], "")
        self.assertEqual(settings["LLM_MODEL"], "")
        self.assertNotIn("UNKNOWN_SETTING", settings)
        self.assertNotIn("ANOTHER_UNKNOWN", settings)
        self.assertEqual(len(settings), 6)

    def test_explicit_none_value_maps_to_empty(self):
        self.write_env("GEMINI_API_KEY=chave-ficticia-arquivo\n")
        settings = load_settings(self.root, environ={"GEMINI_API_KEY": None})
        self.assertEqual(settings["GEMINI_API_KEY"], "")


if __name__ == "__main__":
    unittest.main()
