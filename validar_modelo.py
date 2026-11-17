"""Validação real com uma pergunta do material demonstrativo."""

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
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provedor", choices=["gemini", "ollama"], default=os.getenv("LLM_PROVIDER", "gemini"))
    parser.add_argument("--modelo", default="")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--saida", type=Path, default=ROOT / "output" / "validacao-modelo.json")
    args = parser.parse_args()
    if args.saida.exists():
        parser.error("A saída já existe. Use outro nome para preservar o registro.")
    model = args.modelo or os.getenv("LLM_MODEL" if args.provedor == "gemini" else "OLLAMA_MODEL", "")
    config = ProviderConfig(args.provedor, model, os.getenv("GEMINI_API_KEY", ""), os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"), args.timeout)
    config.validate()
    result = run_query("Como funciona a geração aumentada por recuperação RAG?", DocumentIndex(split_pages(demo_pages())), config)
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(json.dumps(result.export(DEMO_NAME), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Estado: {result.status}; tempo total: {result.elapsed_seconds} s; modelo: {model}")
    print(result.text)
    print(f"Registro: {args.saida}")
    return 0 if result.status == "generated" else 1


if __name__ == "__main__":
    raise SystemExit(main())
