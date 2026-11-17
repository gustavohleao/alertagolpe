import json
import unittest
from unittest.mock import patch

from estudapdf.document import Chunk
from estudapdf.providers import Generation, ProviderConfig, ProviderError
from estudapdf.retrieval import DocumentIndex
from estudapdf.tutor import TutorError, create_round, evaluate, progress_rows


class TutorTests(unittest.TestCase):
    def setUp(self):
        self.index = DocumentIndex([Chunk("P1-T1", 1, "RAG recupera trechos antes de gerar respostas.")])
        self.config = ProviderConfig("gemini", "test", "segredo")
        self.items = [{"question": f"Como funciona RAG? {i}", "expected": "Recupera e gera.",
                       "criteria": ["Explica recuperação", "Explica geração"], "sources": ["P1-T1"]} for i in range(3)]

    def generation(self, value):
        return Generation(json.dumps(value), "test", 0.1, {})

    @patch("estudapdf.tutor.generate")
    def test_no_consent_or_no_evidence_never_calls_api(self, gen):
        for topic, consent in [("RAG", False), ("astronomia", True)]:
            with self.assertRaises(TutorError):
                create_round(topic, self.index, self.config, authorized=consent)
        gen.assert_not_called()

    @patch("estudapdf.tutor.generate")
    def test_round_and_feedback_are_grounded_and_score_is_computed(self, gen):
        gen.return_value = self.generation({"exercises": self.items})
        active = create_round("RAG", self.index, self.config, authorized=True)
        self.assertEqual(len(active.exercises), 3)
        self.assertIn("RAG recupera", gen.call_args.args[1])
        gen.return_value = self.generation({"assessable": True, "met": [True, False], "score": 999,
            "feedback": "Faltou geração", "next_step": "Releia a fonte", "sources": ["P1-T1"]})
        result = evaluate(active.exercises[0], "Recupera trechos", active.hits, self.config, authorized=True)
        self.assertEqual(result["score"], 1)
        self.assertNotIn("segredo", json.dumps(result))

    @patch("estudapdf.tutor.generate")
    def test_invalid_citations_and_malformed_json_are_rejected(self, gen):
        for payload in ["not json", json.dumps({"exercises": [dict(item, sources=["P99-T1"]) for item in self.items]})]:
            gen.return_value = Generation(payload, "test", 0, {})
            with self.assertRaises(TutorError):
                create_round("RAG", self.index, self.config, authorized=True)

    @patch("estudapdf.tutor.generate")
    def test_line_breaks_inside_strings_and_surrounding_text_are_tolerated(self, gen):
        # Falha real do Gemini: quebras de linha cruas dentro das strings e do ID.
        raw = json.dumps({"exercises": self.items}, ensure_ascii=False)
        raw = raw.replace("Recupera e gera.", "Recupera\ne gera.").replace('"P1-T1"', '"P1-\nT1"')
        for payload in [raw, "Aqui está o JSON:\n" + raw + "\nFim."]:
            gen.return_value = Generation(payload, "test", 0, {})
            active = create_round("RAG", self.index, self.config, authorized=True)
            self.assertEqual(active.exercises[0].sources, ("P1-T1",))
            self.assertIn("Recupera", active.exercises[0].expected)
        self.assertTrue(gen.call_args.kwargs["json_output"])

    @patch("estudapdf.tutor.generate")
    def test_evaluation_requires_consent_and_valid_boolean_criteria(self, gen):
        gen.return_value = self.generation({"exercises": self.items})
        active = create_round("RAG", self.index, self.config, authorized=True)
        gen.reset_mock()
        with self.assertRaises(TutorError):
            evaluate(active.exercises[0], "resposta", active.hits, self.config)
        gen.assert_not_called()
        gen.return_value = self.generation({"assessable": True, "met": [1, 0]})
        with self.assertRaises(TutorError):
            evaluate(active.exercises[0], "resposta", active.hits, self.config, authorized=True)

    def test_progress_excludes_unassessable_and_prioritizes_gaps(self):
        history = [{"topic": t, "evaluation": {"assessable": a, "score": s}}
                   for t, a, s in [("RAG", True, 1), ("RAG", True, 2), ("Busca", True, 0), ("Outro", False, None)]]
        rows = progress_rows(history)
        self.assertEqual([r["Assunto"] for r in rows], ["Busca", "RAG"])
        self.assertEqual(rows[1]["Critérios atendidos (%)"], 75)

    @patch("estudapdf.tutor.generate", side_effect=ProviderError("Serviço indisponível"))
    def test_provider_failure_has_no_fake_round(self, gen):
        with self.assertRaises(ProviderError):
            create_round("RAG", self.index, self.config, authorized=True)
