"""Empacota somente código e materiais explicitamente permitidos."""

from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
FILES = ["app.py", "README.md", "requirements.txt", "requirements-lock.txt", ".env.example", ".gitignore", "iniciar.ps1", "verificar.py", "avaliar.py", "validar_modelo.py", "empacotar.py", ".streamlit/config.toml", "data/avaliacao_demo.json"]
FOLDERS = ["src", "tests", "docs", "assets"]
DEMO_RECORDS = ["avaliacao-demo.json", "validacao-ollama.json", "validacao-ollama-1b.json", "validacao-resumo-ollama.json", "validacao-resumo-ollama-v2.json", "validacao-resumo-ollama-v3.json", "ui-desktop.png", "ui-mobile.png", "ui-result.png", "ui-summary.png", "ui-summary-mobile.png"]


def main():
    target = ROOT / "output" / "EstudaPDF-codigo-e-materiais.zip"
    target.parent.mkdir(exist_ok=True)
    candidates = [ROOT / name for name in FILES]
    for name in FOLDERS:
        candidates.extend(path for path in (ROOT / name).rglob("*") if path.is_file() and "__pycache__" not in path.parts and path.suffix in {".py", ".md", ".css", ".svg"})
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(set(candidates)):
            if path.is_file() and not path.is_symlink():
                archive.write(path, path.relative_to(ROOT))
        for name in DEMO_RECORDS:
            path = ROOT / "output" / name
            if path.is_file() and not path.is_symlink():
                archive.write(path, f"output/{name}")
    print(f"Pacote criado: {target}")
    print("Excluídos: .env, runtime, PDFs e consultas particulares. Incluídos registros e capturas conhecidos da demo. Revise antes de entregar.")


if __name__ == "__main__":
    main()
