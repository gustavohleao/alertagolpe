"""Recuperação lexical local: TF-IDF e similaridade do cosseno."""

from __future__ import annotations

from dataclasses import dataclass
import math

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .document import Chunk


@dataclass(frozen=True)
class SearchHit:
    chunk: Chunk
    score: float


class DocumentIndex:
    """Índice de um documento, sem treinamento de classificador ou embeddings.

    Similaridade mede coincidência de vocabulário ponderado. Não é uma
    probabilidade de acerto e não resolve sinônimos por significado.
    """

    def __init__(self, chunks: list[Chunk]):
        if not chunks or any(not chunk.text.strip() for chunk in chunks):
            raise ValueError("É necessário ao menos um trecho com texto para criar o índice.")
        if len({chunk.id for chunk in chunks}) != len(chunks):
            raise ValueError("Os identificadores dos trechos devem ser únicos.")
        self.chunks = tuple(chunks)
        self.vectorizer = TfidfVectorizer(
            strip_accents="unicode",
            lowercase=True,
            ngram_range=(1, 2),
            sublinear_tf=True,
        )
        try:
            self.matrix = self.vectorizer.fit_transform(chunk.text for chunk in self.chunks)
        except ValueError as exc:
            raise ValueError(
                "O documento não contém palavras suficientes para a busca. "
                "Use um PDF com texto legível."
            ) from exc

    def search(
        self, question: str, top_k: int = 3, min_score: float = 0.05
    ) -> list[SearchHit]:
        if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k <= 0:
            raise ValueError("A quantidade de resultados deve ser um inteiro positivo.")
        if (
            isinstance(min_score, bool)
            or not isinstance(min_score, (int, float))
            or not math.isfinite(min_score)
            or not 0 <= min_score <= 1
        ):
            raise ValueError("A similaridade mínima deve estar entre zero e um.")
        if not isinstance(question, str):
            raise ValueError("A pergunta deve ser um texto.")
        if not question.strip():
            return []
        question_vector = self.vectorizer.transform([question])
        if question_vector.nnz == 0:
            return []
        scores = cosine_similarity(question_vector, self.matrix).ravel()
        # Ordenação estável torna empates reproduzíveis na ordem dos trechos.
        ranked_indices = sorted(range(len(scores)), key=lambda i: (-float(scores[i]), i))
        results: list[SearchHit] = []
        seen: set[str] = set()
        for index in ranked_indices:
            score = float(scores[index])
            if score <= 0 or score < min_score:
                continue
            chunk = self.chunks[index]
            # Repetições textuais exatas não ocupam todo o contexto enviado à IA.
            normalized = " ".join(chunk.text.casefold().split())
            if normalized in seen:
                continue
            results.append(SearchHit(chunk=chunk, score=score))
            seen.add(normalized)
            if len(results) == top_k:
                break
        return results

