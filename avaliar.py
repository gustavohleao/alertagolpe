"""Avaliação controlada do exemplo interno. Sem --gerar, não usa API."""

import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv

from estudapdf.demo import DEMO_NAME, demo_pages
from estudapdf.document import split_pages
from estudapdf.providers import ProviderConfig
from estudapdf.retrieval import DocumentIndex
from estudapdf.service import run_query


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gerar", action="store_true", help="Faz chamadas reais ao provedor configurado em .env; pode consumir cota/créditos e envia as perguntas e trechos demonstrativos.")
    parser.add_argument("--saida", type=Path, default=ROOT / "output" / "avaliacao-demo.json")
    args = parser.parse_args()
    load_dotenv(ROOT / ".env")
    config = None
    if args.gerar:
        provider = os.getenv("LLM_PROVIDER", "gemini")
        config = ProviderConfig(provider=provider, model=os.getenv("LLM_MODEL" if provider == "gemini" else "OLLAMA_MODEL", ""), api_key=os.getenv("GEMINI_API_KEY", ""), base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"), timeout=float(os.getenv("LLM_TIMEOUT_SECONDS", "90")))
        config.validate()
    if args.saida.exists():
        parser.error("A saída já existe. Escolha outro nome para preservar o registro anterior.")
    index = DocumentIndex(split_pages(demo_pages()))
    cases = json.loads((ROOT / "data" / "avaliacao_demo.json").read_text(encoding="utf-8"))
    records = []
    for case in cases:
        result = run_query(case["pergunta"], index, config)
        found = {hit.chunk.page for hit in result.hits}
        expected = set(case["secoes_esperadas"])
        record = {"caso": case, "secao_esperada_no_top3": bool(expected & found) if expected else None, "consulta": result.export(DEMO_NAME), "revisao_humana_da_resposta": "pendente"}
        records.append(record)
        print(f"Caso {case['id']}: {result.status}; seções recuperadas: {sorted(found)}")
    positive = [record for record in records if record["secao_esperada_no_top3"] is not None]
    summary = {"modo": "geracao_real" if args.gerar else "somente_recuperacao", "fonte": "Texto demonstrativo assistido por IA, não um PDF ou benchmark independente.", "casos": len(records), "perguntas_com_secao_de_referencia": len(positive), "secao_de_referencia_no_top3": sum(record["secao_esperada_no_top3"] for record in positive), "nota": "Mede somente presença da seção esperada entre até três trechos neste exemplo controlado. Não mede correção de respostas nem desempenho em PDFs reais.", "registros": records}
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Resultado salvo em {args.saida}")
    print(f"Seção esperada no top 3: {summary['secao_de_referencia_no_top3']}/{len(positive)} perguntas com referência.")


if __name__ == "__main__":
    main()
