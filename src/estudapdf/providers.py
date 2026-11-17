"""Integrações HTTP reais. Sem respostas simuladas como fallback."""

from dataclasses import dataclass, field
import re
from time import perf_counter
from urllib.parse import urlsplit

import httpx


class ProviderError(RuntimeError):
    """Erro público sem chave, URL autenticada ou corpo de resposta privado."""


def _normalize_api_key(value: str, *, missing_message: str = "Configure a chave Gemini localmente para gerar respostas.") -> str:
    """Remove espaços externos e rejeita separadores no interior do segredo."""
    key = value.strip()
    if not key:
        raise ProviderError(missing_message)
    if any(char.isspace() for char in key):
        raise ProviderError(
            "A chave Gemini contém espaços ou quebras de linha no meio. "
            "Cole apenas o valor da chave, sem espaços internos."
        )
    return key


@dataclass(frozen=True)
class ProviderConfig:
    provider: str
    model: str
    api_key: str = field(default="", repr=False)
    base_url: str = "http://localhost:11434"
    timeout: float = 90

    def validate(self) -> None:
        if self.provider not in {"gemini", "ollama"}:
            raise ProviderError("Selecione Gemini ou Ollama.")
        if not self.model.strip():
            raise ProviderError("Informe o nome do modelo antes de gerar.")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,150}", self.model):
            raise ProviderError("Nome de modelo inválido.")
        if not 5 <= self.timeout <= 300:
            raise ProviderError("O tempo de espera deve estar entre 5 e 300 segundos.")
        if self.provider == "gemini":
            _normalize_api_key(self.api_key)
            if "/" in self.model.removeprefix("models/") or ":" in self.model:
                raise ProviderError("Use apenas o identificador do modelo Gemini.")
        else:
            local_ollama_url(self.base_url)


@dataclass(frozen=True)
class Generation:
    text: str
    model: str
    elapsed_seconds: float
    usage: dict


def local_ollama_url(value: str) -> str:
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        raise ProviderError("Endereço local do Ollama inválido. Confira o host e a porta.") from None
    if (
        parsed.scheme not in {"http", "https"}
        or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
        or port == 0
    ):
        raise ProviderError("Use um endereço local do Ollama, como http://localhost:11434.")
    return value.rstrip("/")


def _request(client: httpx.Client, method: str, url: str, **kwargs) -> dict:
    try:
        response = client.request(method, url, **kwargs)
        response.raise_for_status()
    except httpx.TimeoutException:
        raise ProviderError("O modelo excedeu o tempo de espera. Nenhuma resposta foi substituída.") from None
    except httpx.HTTPStatusError as exc:
        code = exc.response.status_code
        messages = {
            400: "O provedor recusou os parâmetros. Confira o modelo e a configuração.",
            401: "Autenticação recusada. Confira a chave localmente.",
            403: "Acesso recusado. Confira a chave e a disponibilidade do modelo na conta.",
            404: "Modelo ou serviço não encontrado. Confira o identificador e o provedor.",
            429: "Limite de uso ou cota atingido. Confira sua conta antes de tentar novamente.",
        }
        raise ProviderError(messages.get(code, f"Serviço indisponível (HTTP {code}). Tente novamente mais tarde.")) from None
    except (httpx.RequestError, httpx.InvalidURL):
        raise ProviderError("Não foi possível conectar ao provedor. Confira a conexão e se o serviço está ativo.") from None
    try:
        data = response.json()
    except ValueError:
        raise ProviderError("O provedor retornou um formato de resposta inválido.") from None
    if not isinstance(data, dict):
        raise ProviderError("O provedor retornou uma resposta inesperada.")
    return data


def generate(system: str, prompt: str, config: ProviderConfig, *, client: httpx.Client | None = None) -> Generation:
    config.validate()
    api_key = _normalize_api_key(config.api_key) if config.provider == "gemini" else ""
    started = perf_counter()
    owned = client is None
    connection = client or httpx.Client(timeout=config.timeout, follow_redirects=False, trust_env=config.provider != "ollama")
    try:
        if config.provider == "gemini":
            model = config.model.removeprefix("models/")
            data = _request(
                connection,
                "POST",
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                headers={"x-goog-api-key": api_key},
                json={
                    "systemInstruction": {"parts": [{"text": system}]},
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.2, "maxOutputTokens": 4096},
                },
            )
            candidates = data.get("candidates")
            if not isinstance(candidates, list) or not candidates or not isinstance(candidates[0], dict):
                raise ProviderError("O modelo não retornou texto; a solicitação pode ter sido bloqueada.")
            candidate = candidates[0]
            if candidate.get("finishReason") != "STOP":
                raise ProviderError("A geração foi interrompida ou bloqueada. A resposta incompleta não será exibida.")
            content = candidate.get("content")
            parts = content.get("parts", []) if isinstance(content, dict) else []
            if not isinstance(parts, list):
                raise ProviderError("O modelo retornou conteúdo inesperado.")
            text = "\n".join(
                part["text"] for part in parts
                if isinstance(part, dict) and isinstance(part.get("text"), str) and not part.get("thought")
            ).strip()
            usage = data.get("usageMetadata", {})
        else:
            data = _request(
                connection,
                "POST",
                f"{local_ollama_url(config.base_url)}/api/chat",
                json={
                    "model": config.model,
                    "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {"temperature": 0.2, "num_predict": 800, "num_ctx": 8192},
                },
            )
            if data.get("done") is not True or data.get("done_reason") not in {None, "stop"}:
                raise ProviderError("A geração local não foi concluída. A resposta parcial não será exibida.")
            message = data.get("message")
            text = message.get("content", "") if isinstance(message, dict) else ""
            if not isinstance(text, str):
                raise ProviderError("O modelo local retornou conteúdo inesperado.")
            usage = {name: data[name] for name in ("prompt_eval_count", "eval_count") if name in data}
        if not text.strip():
            raise ProviderError("O modelo retornou uma resposta vazia.")
        return Generation(text.strip(), config.model, round(perf_counter() - started, 3), usage if isinstance(usage, dict) else {})
    finally:
        if owned:
            connection.close()


def list_models(provider: str, *, api_key: str = "", base_url: str = "http://localhost:11434", client: httpx.Client | None = None) -> list[str]:
    """Consulta explícita na interface; não envia documentos nem faz geração."""
    if provider == "gemini":
        api_key = _normalize_api_key(api_key, missing_message="Informe sua chave localmente para consultar os modelos.")
    owned = client is None
    connection = client or httpx.Client(timeout=20, follow_redirects=False, trust_env=provider != "ollama")
    try:
        if provider == "gemini":
            data = _request(connection, "GET", "https://generativelanguage.googleapis.com/v1beta/models", headers={"x-goog-api-key": api_key}, params={"pageSize": 100})
            raw_models = data.get("models", [])
            if not isinstance(raw_models, list):
                raise ProviderError("O provedor retornou uma lista de modelos inválida.")
            models = [item["name"].removeprefix("models/") for item in raw_models if isinstance(item, dict) and isinstance(item.get("name"), str) and isinstance(item.get("supportedGenerationMethods"), list) and "generateContent" in item["supportedGenerationMethods"]]
        elif provider == "ollama":
            data = _request(connection, "GET", f"{local_ollama_url(base_url)}/api/tags")
            raw_models = data.get("models", [])
            if not isinstance(raw_models, list):
                raise ProviderError("O serviço local retornou uma lista de modelos inválida.")
            models = [item.get("name", "") for item in raw_models if isinstance(item, dict)]
        else:
            raise ProviderError("Provedor inválido.")
        return sorted({model for model in models if isinstance(model, str) and model})
    finally:
        if owned:
            connection.close()
