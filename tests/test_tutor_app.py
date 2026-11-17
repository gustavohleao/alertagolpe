from pathlib import Path
import os
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

from estudapdf.tutor import Exercise, Round
from estudapdf.document import Chunk
from estudapdf.retrieval import SearchHit


class TutorAppTests(unittest.TestCase):
    def test_round_answer_feedback_and_document_reset(self):
        exercise = Exercise("RAG", "Como funciona?", "Recupera e gera", ("Recuperação", "Geração"), ("P1-T1",))
        active = Round("RAG", [exercise] * 3, [SearchHit(Chunk("P1-T1", 1, "RAG recupera e gera."), .9)])
        result = {"assessable": True, "met": [True, False], "score": 1,
                  "feedback": "Explique geração", "next_step": "Releia", "sources": ["P1-T1"]}
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake", "LLM_MODEL": "test"}), \
             patch("estudapdf.tutor_ui.create_round", return_value=active) as prepare, \
             patch("estudapdf.tutor_ui.evaluate", return_value=result):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run()
            app.text_input(key="tutor_topic").set_value("RAG")
            next(b for b in app.button if b.label == "Preparar rodada de revisão").click().run()
            prepare.assert_not_called()
            next(c for c in app.checkbox if "minhas respostas" in c.label).check().run()
            next(b for b in app.button if b.label == "Preparar rodada de revisão").click().run()
            self.assertFalse(app.exception)
            self.assertFalse(any(t.value == "Recupera e gera" for t in app.text))
            app.text_area(key="tutor_text_1_0").set_value("Recupera trechos")
            next(b for b in app.button if b.label == "Avaliar minha resposta").click().run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.session_state["tutor_history"]), 1)
            self.assertTrue(any(t.value == "Explique geração" for t in app.text))
            next(b for b in app.button if b.label == "Limpar sessão").click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state["tutor_history"], [])
