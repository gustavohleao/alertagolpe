from pathlib import Path
import os
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest

from estudapdf.document import Chunk
from estudapdf.summary import SummaryError


class SummaryAppTests(unittest.TestCase):
    def app(self):
        return AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=25).run()

    def result(self):
        text = "Resumo [P1-R1] ![imagem](https://exemplo.invalid/pixel)"
        return SimpleNamespace(
            text=text,
            pages=(1, 2, 3, 4),
            calls_completed=1,
            elapsed_seconds=0.01,
            provider="gemini",
            model="modelo-teste",
            citations=("P1-R1",),
            source_chunks=(Chunk("P1-R1", 1, "Texto educativo de referência.", "Seção"),),
            warning="",
            export=Mock(return_value={"tipo": "resumo", "texto": text}),
        )

    def summary_button(self, app):
        return next(button for button in app.button if button.label == "Gerar resumo do material")

    def test_summary_is_plain_text_and_range_change_invalidates_it(self):
        result = self.result()
        with patch.dict(os.environ, {"LLM_PROVIDER": "gemini", "LLM_MODEL": "modelo-teste", "GEMINI_API_KEY": "chave-ficticia"}), patch("estudapdf.frontend.summarize", return_value=result) as summarize:
            app = self.app()

            next(box for box in app.checkbox if box.label.startswith("Autorizo enviar todo o texto")).check().run()
            self.summary_button(app).click().run()
            self.assertFalse(app.exception)
            self.assertTrue(any(item.value == result.text for item in app.text))
            self.assertFalse(any("https://exemplo.invalid/pixel" in item.value for item in app.markdown))
            summarize.assert_called_once()
            app.slider[0].set_value((1, 2)).run()
            self.assertFalse(app.exception)
            self.assertFalse(any(item.value == result.text for item in app.text))
            summarize.assert_called_once()

    def test_gemini_requires_its_own_summary_consent(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "gemini", "GEMINI_API_KEY": "chave-ficticia", "LLM_MODEL": "modelo-teste"}), patch("estudapdf.frontend.summarize", return_value=self.result()) as summarize:
            app = self.app()

            self.summary_button(app).click().run()
            self.assertFalse(app.exception)
            self.assertTrue(any("Autorize o envio do texto selecionado" in item.value for item in app.error))
            summarize.assert_not_called()
            consent = next(box for box in app.checkbox if box.label.startswith("Autorizo enviar todo o texto"))
            consent.check().run()
            # A autorização de perguntas permanece desmarcada: são ações distintas.
            query_consent = next(box for box in app.checkbox if box.label.startswith("Autorizo enviar minha pergunta"))
            self.assertFalse(query_consent.value)
            next(box for box in app.checkbox if box.label.startswith("Autorizo enviar todo o texto")).check().run()
            self.summary_button(app).click().run()
            self.assertFalse(app.exception)
            summarize.assert_called_once()
            self.assertTrue(summarize.call_args.kwargs["allow_external"])

    def test_failed_new_summary_does_not_display_old_success(self):
        result = self.result()
        with patch.dict(os.environ, {"LLM_PROVIDER": "gemini", "LLM_MODEL": "modelo-teste", "GEMINI_API_KEY": "chave-ficticia"}), patch("estudapdf.frontend.summarize", side_effect=[result, SummaryError("Falha após uma chamada.")]):
            app = self.app()

            next(box for box in app.checkbox if box.label.startswith("Autorizo enviar todo o texto")).check().run()
            self.summary_button(app).click().run()
            self.assertTrue(any(item.value == result.text for item in app.text))
            next(box for box in app.checkbox if box.label.startswith("Autorizo enviar todo o texto")).check().run()
            self.summary_button(app).click().run()
            self.assertFalse(app.exception)
            self.assertTrue(any("Falha após uma chamada" in item.value for item in app.error))
            self.assertFalse(any(item.value == result.text for item in app.text))

    def test_summary_without_citations_is_labeled_and_shows_input_not_fake_sources(self):
        result = self.result()
        result.citations = ()
        result.warning = "O modelo não indicou referências. Confira o material original."
        with patch.dict(os.environ, {"LLM_PROVIDER": "gemini", "LLM_MODEL": "modelo-teste", "GEMINI_API_KEY": "chave-ficticia"}), patch("estudapdf.frontend.summarize", return_value=result):
            app = self.app()

            next(box for box in app.checkbox if box.label.startswith("Autorizo enviar todo o texto")).check().run()
            self.summary_button(app).click().run()
            self.assertFalse(app.exception)
            self.assertTrue(any(item.value == result.warning for item in app.warning))
            source_selector = next(item for item in app.selectbox if item.label == "Consultar trecho processado")
            self.assertEqual(len(source_selector.options), 1)
            self.assertTrue(any("sem atribuir citações" in item.value for item in app.caption))


if __name__ == "__main__":
    unittest.main()
