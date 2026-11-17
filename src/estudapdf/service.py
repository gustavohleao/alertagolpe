"""Orquestração: recuperar antes de gerar; não chamar API sem evidência."""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import re
from time import perf_counter

from .prompts import PROMPT_VERSION, SYSTEM_PROMPT, build_prompt
from .providers import ProviderConfig, ProviderError, generate
from .retrieval import DocumentIndex, SearchHit


@dataclass
class QueryResult:
    question: str
    status: str
    text: str
    hits: list[SearchHit]
    elapsed_seconds: float
    provider: str = "nenhum"
    model: str = ""
    prompt: str = ""
    warning: str = ""
    usage: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def export(self, source_name: str) -> dict:
        return {
            "aplicacao": "EstudaPDF",
            "versao_prompt": PROMPT_VERSION,
            "fonte": source_name,
            "sistema_prompt": SYSTEM_PROMPT if self.prompt else "",
            **asdict(self),
            "nota": "Trechos e respostas podem conter dados do documento. Compartilhe somente material autorizado. Similaridade não é probabilidade de correção.",
        }


def run_query(question: str, index: DocumentIndex, config: ProviderConfig | None = None) -> QueryResult:
    question = question.strip()
    if not question:
        raise ValueError("Digite uma pergunta sobre o material.")
    if len(question) > 1200:
        raise ValueError("Use uma pergunta com no máximo 1.200 caracteres.")
    start = perf_counter()
    hits = index.search(question, top_k=3, min_score=0.05)
    elapsed = lambda: round(perf_counter() - start, 3)
    if not hits:
        return QueryResult(question, "no_evidence", "Não encontrei trechos com correspondência suficiente. Tente usar os termos do material. Isso não prova que a informação esteja ausente do documento.", [], elapsed())
    if config is None:
        return QueryResult(question, "search_only", "Confira os trechos encontrados ao lado. Esta consulta fez somente busca no material; nenhuma resposta foi gerada por IA.", hits, elapsed())
    prompt = build_prompt(question, hits)
    try:
        generation = generate(SYSTEM_PROMPT, prompt, config)
    except ProviderError as exc:
        return QueryResult(question, "provider_error", str(exc), hits, elapsed(), config.provider, config.model, prompt)
    allowed = {hit.chunk.id for hit in hits}
    citations = set(re.findall(r"\[(P\d+-T\d+)\]", generation.text))
    if citations - allowed:
        return QueryResult(question, "invalid_citations", "O modelo citou uma referência que não foi fornecida. A resposta foi retida; consulte os trechos e tente novamente.", hits, elapsed(), config.provider, config.model, prompt, usage=generation.usage)
    warning = "As referências precisam sustentar as afirmações. Confira o texto original; a IA pode interpretar os trechos incorretamente."
    refusal = "não encontrei informação suficiente" in generation.text.casefold()
    if not citations and not refusal:
        warning = "A resposta não trouxe referências no formato esperado. Confira todas as afirmações nos trechos antes de usar."
    return QueryResult(question, "generated", generation.text, hits, elapsed(), config.provider, config.model, prompt, warning, generation.usage)
