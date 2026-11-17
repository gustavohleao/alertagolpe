from pathlib import Path
import os
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


class ServerConfigAppTests(unittest.TestCase):
    def app(self):
        return AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=25).run()

    def test_gemini_key_is_loaded_without_password_or_secret_display(self):
        key = "chave-ficticia-apenas-no-servidor"
        with patch.dict(os.environ, {"LLM_PROVIDER": "gemini", "GEMINI_API_KEY": key, "LLM_MODEL": "modelo-teste"}), patch("estudapdf.frontend.list_models", return_value=["modelo-teste"]) as listing:
            app = self.app()
            app.radio[0].set_value("Resposta com IA").run()
            self.assertFalse(app.exception)
            self.assertFalse(any("Chave" in item.label or "chave" in item.label for item in app.text_input))
            visible_text = [str(item.value) for group in (app.caption, app.text, app.markdown, app.warning, app.error) for item in group]
            self.assertFalse(any(key in value for value in visible_text))
            next(button for button in app.button if button.label == "Consultar modelos disponíveis").click().run()
            self.assertFalse(app.exception)
            listing.assert_called_once_with("gemini", api_key=key, base_url="http://localhost:11434")

    def test_missing_server_key_disables_model_lookup(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "gemini", "GEMINI_API_KEY": "", "LLM_MODEL": ""}), patch("estudapdf.frontend.list_models") as listing:
            app = self.app()
            app.radio[0].set_value("Resposta com IA").run()
            self.assertFalse(app.exception)
            button = next(button for button in app.button if button.label == "Consultar modelos disponíveis")
            self.assertTrue(button.disabled)
            self.assertTrue(any("Defina GEMINI_API_KEY" in item.value for item in app.warning))
            listing.assert_not_called()

    def test_new_server_key_invalidates_cached_models_on_rerun(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "gemini", "GEMINI_API_KEY": "fake-key-A", "LLM_MODEL": "modelo-teste"}), patch("estudapdf.frontend.list_models", side_effect=[["modelo-A"], ["modelo-B"]]) as listing:
            app = self.app()
            app.radio[0].set_value("Resposta com IA").run()
            next(button for button in app.button if button.label == "Consultar modelos disponíveis").click().run()
            self.assertTrue(any(item.label == "Modelos encontrados" for item in app.selectbox))
            os.environ["GEMINI_API_KEY"] = "fake-key-B"
            app.run()
            self.assertFalse(app.exception)
            self.assertFalse(any(item.label == "Modelos encontrados" for item in app.selectbox))
            next(button for button in app.button if button.label == "Consultar modelos disponíveis").click().run()
            self.assertFalse(app.exception)
            self.assertEqual(listing.call_args.kwargs["api_key"], "fake-key-B")


if __name__ == "__main__":
    unittest.main()
