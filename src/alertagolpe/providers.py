"""Integrações HTTP reais. Sem respostas simuladas como fallback."""

from dataclasses import dataclass, field
import random
import re
import time
from time import perf_counter

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
        if self.provider != "gemini":
            raise ProviderError("A geração está disponível exclusivamente pela API Gemini.")
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


@dataclass(frozen=True)
class Generation:
    text: str
    model: str
    elapsed_seconds: float
    usage: dict


# Sobrecarga momentânea do provedor (ex.: 503 "high demand") costuma passar em
# segundos. Repetimos a mesma requisição poucas vezes; erros de chave, cota (429)
# e parâmetros não são repetidos. Uma requisição travada até o tempo limite é
# repetida uma única vez, sem espera adicional.
TRANSIENT_STATUS = {500, 502, 503, 504}
RETRY_DELAYS = (2.0, 5.0, 10.0)
MAX_RETRY_AFTER = 15.0
TIMEOUT_RETRIES = 1


def _retry_delay(response: httpx.Response, attempt: int) -> float:
    try:
        hinted = float(response.headers.get("retry-after", ""))
    except ValueError:
        hinted = 0.0
    base = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
    return min(max(base, hinted), MAX_RETRY_AFTER) + random.uniform(0, 0.5)


def _request(client: httpx.Client, method: str, url: str, *, sleep=None, **kwargs) -> dict:
    try:
        timeouts = 0
        attempt = 0
        while True:
            try:
                response = client.request(method, url, **kwargs)
            except httpx.TimeoutException:
                if timeouts >= TIMEOUT_RETRIES:
                    raise
                timeouts += 1
                continue
            if response.status_code not in TRANSIENT_STATUS or attempt == len(RETRY_DELAYS):
                break
            (sleep or time.sleep)(_retry_delay(response, attempt))
            attempt += 1
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


def generate(system: str, prompt: str, config: ProviderConfig, *, client: httpx.Client | None = None, json_output: bool = False) -> Generation:
    config.validate()
    api_key = _normalize_api_key(config.api_key)
    started = perf_counter()
    owned = client is None
    connection = client or httpx.Client(timeout=config.timeout, follow_redirects=False, trust_env=True)
    try:
        model = config.model.removeprefix("models/")
        data = _request(
            connection,
            "POST",
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            headers={"x-goog-api-key": api_key},
            json={
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                # Modo JSON da API: evita quebras de linha soltas e texto fora do objeto.
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 4096,
                                     **({"responseMimeType": "application/json"} if json_output else {})},
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
        if not text.strip():
            raise ProviderError("O modelo retornou uma resposta vazia.")
        return Generation(text.strip(), config.model, round(perf_counter() - started, 3), usage if isinstance(usage, dict) else {})
    finally:
        if owned:
            connection.close()


def list_models(provider: str, *, api_key: str = "", base_url: str = "http://localhost:11434", client: httpx.Client | None = None) -> list[str]:
    """Consulta explícita na interface; não envia documentos nem faz geração."""
    if provider != "gemini":
        raise ProviderError("A geração está disponível exclusivamente pela API Gemini.")
    if provider == "gemini":
        api_key = _normalize_api_key(api_key, missing_message="Informe sua chave localmente para consultar os modelos.")
    owned = client is None
    connection = client or httpx.Client(timeout=20, follow_redirects=False, trust_env=True)
    try:
        if provider == "gemini":
            data = _request(connection, "GET", "https://generativelanguage.googleapis.com/v1beta/models", headers={"x-goog-api-key": api_key}, params={"pageSize": 100})
            raw_models = data.get("models", [])
            if not isinstance(raw_models, list):
                raise ProviderError("O provedor retornou uma lista de modelos inválida.")
            models = [item["name"].removeprefix("models/") for item in raw_models if isinstance(item, dict) and isinstance(item.get("name"), str) and isinstance(item.get("supportedGenerationMethods"), list) and "generateContent" in item["supportedGenerationMethods"]]
        return sorted({model for model in models if isinstance(model, str) and model})
    finally:
        if owned:
            connection.close()
