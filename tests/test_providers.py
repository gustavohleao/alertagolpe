import json
import unittest
from unittest.mock import patch

import httpx

from estudapdf.providers import ProviderConfig, ProviderError, generate, list_models


class ProviderTests(unittest.TestCase):
    """HTTP simulado somente nos testes; não valida contas ou modelos reais."""

    def client(self, handler):
        client = httpx.Client(transport=httpx.MockTransport(handler))
        self.addCleanup(client.close)
        return client

    def test_gemini_request_and_response(self):
        def handler(request):
            self.assertNotIn("chave-ficticia", str(request.url))
            self.assertEqual(request.headers["x-goog-api-key"], "chave-ficticia")
            body = json.loads(request.content)
            self.assertEqual(body["systemInstruction"]["parts"][0]["text"], "sistema")
            self.assertEqual(body["contents"][0]["parts"][0]["text"], "contexto")
            return httpx.Response(200, json={"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": "pensamento", "thought": True}, {"text": "Resposta [P1-T1]"}]}}], "usageMetadata": {"totalTokenCount": 25}})
        result = generate("sistema", "contexto", ProviderConfig("gemini", "models/modelo-teste", "chave-ficticia"), client=self.client(handler))
        self.assertEqual(result.text, "Resposta [P1-T1]")
        self.assertEqual(result.usage["totalTokenCount"], 25)

    def test_ollama_real_protocol_shape(self):
        def handler(request):
            self.assertEqual(str(request.url), "http://localhost:11434/api/chat")
            self.assertFalse(json.loads(request.content)["stream"])
            return httpx.Response(200, json={"message": {"content": "Resposta"}, "done": True, "done_reason": "stop"})
        result = generate("sistema", "prompt", ProviderConfig("ollama", "modelo-local:1b"), client=self.client(handler))
        self.assertEqual(result.text, "Resposta")

    def test_timeout_and_connection_errors_are_sanitized(self):
        for error in [httpx.ReadTimeout("segredo"), httpx.ConnectError("segredo")]:
            with self.subTest(error=type(error)):
                def handler(request):
                    raise error
                with self.assertRaises(ProviderError) as caught:
                    generate("s", "p", ProviderConfig("ollama", "modelo"), client=self.client(handler))
                self.assertNotIn("segredo", str(caught.exception))

    def test_http_error_does_not_expose_body_or_key(self):
        client = self.client(lambda request: httpx.Response(403, text="conteudo-privado chave-ficticia"))
        with self.assertRaises(ProviderError) as caught:
            generate("s", "p", ProviderConfig("gemini", "modelo", "chave-ficticia"), client=client)
        self.assertNotIn("chave-ficticia", str(caught.exception))
        self.assertNotIn("conteudo-privado", str(caught.exception))

    def test_invalid_json_empty_and_truncated_responses(self):
        responses = [
            httpx.Response(200, text="não é JSON"),
            httpx.Response(200, json=[]),
            httpx.Response(200, json={}),
            httpx.Response(200, json={"candidates": [{"finishReason": "MAX_TOKENS", "content": {"parts": [{"text": "incompleto"}]}}]}),
            httpx.Response(200, json={"candidates": [{"finishReason": "STOP", "content": {"parts": []}}]}),
        ]
        for response in responses:
            with self.subTest(response=response.content):
                client = self.client(lambda request: response)
                with self.assertRaises(ProviderError):
                    generate("s", "p", ProviderConfig("gemini", "modelo", "chave"), client=client)

    def test_missing_config_rejected_before_network(self):
        for config in [ProviderConfig("gemini", "modelo"), ProviderConfig("gemini", "", "chave"), ProviderConfig("gemini", "../outro", "chave"), ProviderConfig("ollama", "modelo", base_url="http://example.com"), ProviderConfig("ollama", "modelo", base_url="http://localhost:11434@evil.example"), ProviderConfig("ollama", "modelo", base_url="http://localhost:abc"), ProviderConfig("ollama", "modelo", base_url="http://[::1"), ProviderConfig("ollama", "modelo", base_url="http://localhost:0"), ProviderConfig("outro", "modelo")]:
            with self.subTest(config=repr(config)):
                with self.assertRaises(ProviderError):
                    config.validate()
        self.assertNotIn("segredo", repr(ProviderConfig("gemini", "modelo", "segredo")))

    def test_lists_only_generation_models(self):
        client = self.client(lambda request: httpx.Response(200, json={"models": [{"name": "models/texto", "supportedGenerationMethods": ["generateContent"]}, {"name": "models/embedding", "supportedGenerationMethods": ["embedContent"]}]}))
        self.assertEqual(list_models("gemini", api_key="chave", client=client), ["texto"])

    def test_list_models_trims_key_before_sending_header(self):
        def handler(request):
            self.assertEqual(request.headers["x-goog-api-key"], "chave-ficticia")
            return httpx.Response(200, json={"models": [{"name": "models/texto", "supportedGenerationMethods": ["generateContent"]}]})

        models = list_models("gemini", api_key=" \tchave-ficticia\r\n", client=self.client(handler))
        self.assertEqual(models, ["texto"])

    def test_generate_trims_key_before_sending_header(self):
        def handler(request):
            self.assertEqual(request.headers["x-goog-api-key"], "chave-ficticia")
            return httpx.Response(200, json={"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": "Resposta"}]}}]})

        result = generate("s", "p", ProviderConfig("gemini", "modelo", " \nchave-ficticia\t "), client=self.client(handler))
        self.assertEqual(result.text, "Resposta")

    @patch("estudapdf.providers.httpx.Client")
    def test_internal_key_whitespace_rejected_before_client_or_request(self, client_factory):
        for key in ("chave ficticia", "chave\nficticia", "chave\tficticia", "chave\rficticia", "chave\u00a0ficticia"):
            for operation in ("generate", "list_models"):
                with self.subTest(key=repr(key), operation=operation):
                    with self.assertRaisesRegex(ProviderError, "espaços ou quebras de linha") as caught:
                        if operation == "generate":
                            generate("s", "p", ProviderConfig("gemini", "modelo", key))
                        else:
                            list_models("gemini", api_key=key)
                    self.assertNotIn(key, str(caught.exception))
        client_factory.assert_not_called()

    @patch("estudapdf.providers.httpx.Client")
    def test_missing_keys_rejected_before_client_creation(self, client_factory):
        for key in ("", " \n\t "):
            with self.subTest(key=repr(key)):
                with self.assertRaisesRegex(ProviderError, "Configure a chave Gemini"):
                    generate("s", "p", ProviderConfig("gemini", "modelo", key))
                with self.assertRaisesRegex(ProviderError, "Informe sua chave localmente"):
                    list_models("gemini", api_key=key)
        client_factory.assert_not_called()


if __name__ == "__main__":
    unittest.main()
