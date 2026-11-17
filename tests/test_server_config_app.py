from pathlib import Path
import os
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

class ServerConfigAppTests(unittest.TestCase):
    def test_interface_has_no_ai_configuration_controls(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key", "LLM_MODEL": "modelo-teste"}):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=25).run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.radio), 0)
            self.assertEqual(len(app.text_input), 0)
            self.assertFalse(any(item.label == "Configuração da IA" for item in app.expander))
            self.assertFalse(any(button.label == "Consultar modelos disponíveis" for button in app.button))

    def test_model_is_resolved_on_server_and_cached(self):
        from estudapdf.frontend import _ready_config
        from estudapdf.providers import ProviderConfig
        with patch("estudapdf.frontend.list_models", return_value=["modelo-flash-texto"]):
            config = _ready_config(ProviderConfig("gemini", "", "fake-key"))
            self.assertEqual(config.model, "modelo-flash-texto")
