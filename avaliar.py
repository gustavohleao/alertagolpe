"""Avalia o AlertaGolpe no conjunto avaliacao/mensagens.json.

Uso:  python avaliar.py            (regras locais e IA, se houver chave no .env)
      python avaliar.py --local    (somente regras locais, sem chamadas à API)
      python avaliar.py --conjunto avaliacao/teste-reserva.json   (outro conjunto)

Considera "detectado como golpe" um risco alto ou médio. Salva o resultado de
cada mensagem em output/avaliacao-resultados.json.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from alertagolpe.analyzer import analyze  # noqa: E402
from alertagolpe.providers import ProviderConfig, ProviderError  # noqa: E402
from alertagolpe.settings import load_settings  # noqa: E402


def run(mode: str, messages: list[dict], config, fallbacks: tuple[str, ...] = ()) -> dict:
    rows = []
    for item in messages:
        try:
            result = analyze(item["texto"], config, fallbacks)
            rows.append({"id": item["id"], "rotulo": item["rotulo"], "esperado": item["golpe"], "risco": result.risk,
                         "golpe_previsto": result.scam_id, "pontuacao_local": result.local_score,
                         "segundos": result.elapsed_seconds, "modelo": result.model, "erro": None})
        except (ProviderError, ValueError) as exc:
            rows.append({"id": item["id"], "rotulo": item["rotulo"], "esperado": item["golpe"], "risco": None,
                         "golpe_previsto": None, "pontuacao_local": None, "segundos": None, "erro": str(exc)})
        print(f"  {mode:5} {item['id']}: {rows[-1]['risco'] or 'ERRO'}", flush=True)
    scams = [r for r in rows if r["rotulo"] == "golpe" and r["risco"]]
    legit = [r for r in rows if r["rotulo"] == "legitima" and r["risco"]]
    detected = [r for r in scams if r["risco"] in ("alto", "medio")]
    false_alarm = [r for r in legit if r["risco"] in ("alto", "medio")]
    times = [r["segundos"] for r in rows if r["segundos"] is not None]
    return {
        "modo": mode,
        "golpes_detectados": f"{len(detected)}/{len(scams)}",
        "golpes_como_alto": f"{sum(r['risco'] == 'alto' for r in scams)}/{len(scams)}",
        "tipo_de_golpe_correto": f"{sum(r['golpe_previsto'] == r['esperado'] for r in detected if r['esperado'])}/{sum(1 for r in detected if r['esperado'])}",
        "alarmes_falsos": f"{len(false_alarm)}/{len(legit)}",
        "alarmes_falsos_alto": f"{sum(r['risco'] == 'alto' for r in legit)}/{len(legit)}",
        "acuracia": f"{len(detected) + len(legit) - len(false_alarm)}/{len(scams) + len(legit)}",
        "erros": sum(r["erro"] is not None for r in rows),
        "tempo_medio_s": round(statistics.mean(times), 2) if times else None,
        "tempo_max_s": round(max(times), 2) if times else None,
        "por_mensagem": rows,
    }


def main() -> None:
    source = Path(sys.argv[sys.argv.index("--conjunto") + 1]) if "--conjunto" in sys.argv else ROOT / "avaliacao" / "mensagens.json"
    data = json.loads((source if source.is_absolute() else ROOT / source).read_text(encoding="utf-8"))
    messages = data["mensagens"]
    settings = load_settings(ROOT)
    results = [run("local", messages, None)]
    local_llm = "--provedor" in sys.argv and sys.argv[sys.argv.index("--provedor") + 1] == "ollama"
    if "--local" not in sys.argv and local_llm:
        # Modelo local pelo Ollama (ex.: qwen2.5:3b): sem internet e sem modelos reserva.
        model = settings["OLLAMA_MODEL"].strip() or "qwen2.5:3b"
        results.append(run("ia", messages, ProviderConfig("ollama", model, base_url=settings["OLLAMA_BASE_URL"].strip(), timeout=300)))
        settings["LLM_MODEL"] = f"ollama/{model}"
    elif "--local" not in sys.argv and settings["GEMINI_API_KEY"].strip():
        config = ProviderConfig("gemini", settings["LLM_MODEL"].strip(), settings["GEMINI_API_KEY"].strip(), timeout=90)
        fallbacks = tuple(m.strip() for m in settings["LLM_FALLBACK_MODELS"].split(",") if m.strip())
        results.append(run("ia", messages, config, fallbacks))
    print("\nResumo")
    keys = ["golpes_detectados", "golpes_como_alto", "tipo_de_golpe_correto", "alarmes_falsos", "alarmes_falsos_alto", "acuracia", "erros", "tempo_medio_s", "tempo_max_s"]
    for key in keys:
        print(f"  {key:24}" + "".join(f"{str(r[key]):>12}" for r in results))
    out = ROOT / "output" / ("avaliacao-resultados.json" if "--conjunto" not in sys.argv else f"avaliacao-{source.stem}.json")
    if local_llm:
        out = out.with_name(out.stem + "-ollama.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"data": datetime.now(timezone.utc).isoformat(), "modelo": settings["LLM_MODEL"],
                               "conjunto": data["descricao"], "resultados": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDetalhes salvos em {out}")


if __name__ == "__main__":
    main()
