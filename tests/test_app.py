from pathlib import Path
import os
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from estudapdf.providers import Generation


class AppTests(unittest.TestCase):
    def app(self):
        return AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=25).run()

    def test_demo_and_search_without_key(self):
        app = self.app()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[0].value, "4")
        app.text_area[0].set_value("Como funciona o RAG?")
        next(button for button in app.button if button.label == "Encontrar trechos").click().run()
        self.assertFalse(app.exception)
        self.assertTrue(any("nenhuma resposta foi gerada" in item.value for item in app.info))
        self.assertTrue(any("P2-" in item.label for item in app.expander))

    def test_empty_input_is_explained(self):
        app = self.app()
        next(button for button in app.button if button.label == "Encontrar trechos").click().run()
        self.assertFalse(app.exception)
        self.assertTrue(any("Digite uma pergunta" in item.value for item in app.warning))

    def test_no_document_shows_upload_guidance(self):
        app = self.app()
        next(box for box in app.checkbox if box.label == "Usar material de demonstração").uncheck().run()
        self.assertFalse(app.exception)
        self.assertTrue(any("Carregue um PDF" in item.value for item in app.info))

    def test_generated_content_is_plain_text_not_remote_markdown(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "ollama", "OLLAMA_MODEL": "modelo-teste"}), patch("estudapdf.service.generate") as generate:
            content = "Resposta [P2-T1] ![imagem](https://exemplo.invalid/pixel)"
            generate.return_value = Generation(content, "modelo-teste", 0.01, {})
            app = self.app()
            app.radio[0].set_value("Resposta com IA").run()
            app.text_area[0].set_value("Como funciona o RAG?")
            next(button for button in app.button if button.label == "Buscar e responder").click().run()
            self.assertFalse(app.exception)
            self.assertTrue(any(item.value == content for item in app.text))
            self.assertFalse(any("https://exemplo.invalid/pixel" in item.value for item in app.markdown))


if __name__ == "__main__":
    unittest.main()
