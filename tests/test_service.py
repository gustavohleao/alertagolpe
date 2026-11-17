import unittest
from unittest.mock import patch

from estudapdf.document import Chunk
from estudapdf.providers import Generation, ProviderConfig, ProviderError
from estudapdf.retrieval import DocumentIndex
from estudapdf.service import run_query


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.index = DocumentIndex([Chunk("P3-T1", 3, "O processo RAG recupera trechos relevantes antes de gerar a resposta.")])
        self.config = ProviderConfig("gemini", "modelo-teste", "chave-secreta")

    @patch("estudapdf.service.generate")
    def test_search_only_never_calls_provider(self, generate):
        result = run_query("RAG", self.index)
        self.assertEqual(result.status, "search_only")
        self.assertEqual(result.hits[0].chunk.page, 3)
        generate.assert_not_called()

    @patch("estudapdf.service.generate")
    def test_no_evidence_never_calls_provider(self, generate):
        result = run_query("astronomia", self.index, self.config)
        self.assertEqual(result.status, "no_evidence")
        generate.assert_not_called()

    @patch("estudapdf.service.generate")
    def test_grounded_context_and_export_do_not_include_key(self, generate):
        generate.return_value = Generation("O RAG recupera trechos [P3-T1].", "modelo-teste", 0.1, {})
        result = run_query("Como funciona RAG?", self.index, self.config)
        self.assertEqual(result.status, "generated")
        self.assertIn("P3-T1", result.prompt)
        self.assertIn("trechos relevantes", result.prompt)
        self.assertNotIn("chave-secreta", str(result.export("fonte.pdf")))

    @patch("estudapdf.service.generate")
    def test_invalid_citation_is_withheld(self, generate):
        generate.return_value = Generation("Afirmação [P99-T9].", "modelo", 0.1, {})
        result = run_query("RAG", self.index, self.config)
        self.assertEqual(result.status, "invalid_citations")
        self.assertNotIn("Afirmação", result.text)

    @patch("estudapdf.service.generate")
    def test_missing_citation_warns_but_does_not_claim_validity(self, generate):
        generate.return_value = Generation("Resposta sem referência.", "modelo", 0.1, {})
        result = run_query("RAG", self.index, self.config)
        self.assertEqual(result.status, "generated")
        self.assertIn("não trouxe referências", result.warning)

    @patch("estudapdf.service.generate", side_effect=ProviderError("Cota atingida"))
    def test_failure_preserves_evidence_without_fake_answer(self, generate):
        result = run_query("RAG", self.index, self.config)
        self.assertEqual(result.status, "provider_error")
        self.assertEqual(result.text, "Cota atingida")
        self.assertEqual(len(result.hits), 1)

    def test_empty_and_overlong_questions_are_rejected(self):
        for question in [" ", "x" * 1201]:
            with self.assertRaises(ValueError):
                run_query(question, self.index)


if __name__ == "__main__":
    unittest.main()
