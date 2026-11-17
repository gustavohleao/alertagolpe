"""Testes de relevância lexical, metadados e rejeição de entradas inválidas."""

import unittest

from estudapdf.document import Chunk
from estudapdf.retrieval import DocumentIndex


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.chunks = [
            Chunk("P1-T1", 1, "Aprendizado supervisionado usa exemplos rotulados e classificação."),
            Chunk("P2-T1", 2, "Fotossíntese transforma energia solar em energia química."),
            Chunk("P3-T1", 3, "RAG recupera trechos para fornecer contexto ao modelo generativo.", "Seção"),
        ]
        self.index = DocumentIndex(self.chunks)

    def test_retrieves_relevant_passage_and_preserves_metadata(self):
        hits = self.index.search("Como RAG fornece contexto ao modelo?", top_k=1)
        self.assertEqual(hits[0].chunk.id, "P3-T1")
        self.assertEqual(hits[0].chunk.location_label, "Seção")
        self.assertGreater(hits[0].score, 0)

    def test_accent_normalization(self):
        hits = self.index.search("classificacao supervisionado", top_k=1)
        self.assertEqual(hits[0].chunk.page, 1)

    def test_empty_and_out_of_vocabulary_questions_return_no_hits(self):
        self.assertEqual(self.index.search("   "), [])
        self.assertEqual(self.index.search("astronautas exoplanetas"), [])

    def test_zero_threshold_does_not_include_zero_similarity(self):
        hits = self.index.search("fotossintese", min_score=0)
        self.assertEqual([hit.chunk.page for hit in hits], [2])

    def test_scores_are_sorted_and_limit_is_respected(self):
        hits = self.index.search("energia modelo exemplos", top_k=2, min_score=0)
        self.assertEqual(len(hits), 2)
        self.assertGreaterEqual(hits[0].score, hits[1].score)

    def test_exact_duplicates_do_not_fill_context(self):
        index = DocumentIndex([
            Chunk("a", 1, "contexto relevante"),
            Chunk("b", 2, "CONTEXTO relevante"),
            Chunk("c", 3, "Outro contexto diferente"),
        ])
        hits = index.search("contexto", top_k=3, min_score=0)
        self.assertEqual(len(hits), 2)

    def test_invalid_parameters(self):
        for kwargs in ({"top_k": 0}, {"top_k": True}, {"min_score": -0.1}, {"min_score": 2}, {"min_score": float("nan")}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.index.search("RAG", **kwargs)

    def test_empty_document_or_vocabulary_and_duplicate_ids(self):
        for chunks in ([], [Chunk("a", 1, "")], [Chunk("a", 1, "! ?")], [Chunk("a", 1, "texto"), Chunk("a", 2, "outro")]):
            with self.subTest(chunks=chunks), self.assertRaises(ValueError):
                DocumentIndex(chunks)


if __name__ == "__main__":
    unittest.main()
