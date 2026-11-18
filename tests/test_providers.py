import json
import unittest
from unittest.mock import patch

import httpx

from alertagolpe.providers import ProviderConfig, ProviderError, generate, list_models


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

    def test_json_output_requests_json_mime_type(self):
        bodies = []
        def handler(request):
            bodies.append(json.loads(request.content))
            return httpx.Response(200, json={"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": "{}"}]}}]})
        client = self.client(handler)
        generate("s", "p", ProviderConfig("gemini", "modelo", "chave-ficticia"), client=client, json_output=True)
        generate("s", "p", ProviderConfig("gemini", "modelo", "chave-ficticia"), client=client)
        self.assertEqual(bodies[0]["generationConfig"]["responseMimeType"], "application/json")
        self.assertNotIn("responseMimeType", bodies[1]["generationConfig"])

    def test_local_provider_is_rejected(self):
        with self.assertRaises(ProviderError):
            ProviderConfig("ollama", "modelo-local").validate()
        with self.assertRaises(ProviderError):
            list_models("ollama")

    def test_timeout_and_connection_errors_are_sanitized(self):
        for error in [httpx.ReadTimeout("segredo"), httpx.ConnectError("segredo")]:
            with self.subTest(error=type(error)):
                def handler(request):
                    raise error
                with self.assertRaises(ProviderError) as caught:
                    generate("s", "p", ProviderConfig("gemini", "modelo", "chave-ficticia"), client=self.client(handler))
                self.assertNotIn("segredo", str(caught.exception))

    def test_http_error_does_not_expose_body_or_key(self):
        client = self.client(lambda request: httpx.Response(403, text="conteudo-privado chave-ficticia"))
        with self.assertRaises(ProviderError) as caught:
            generate("s", "p", ProviderConfig("gemini", "modelo", "chave-ficticia"), client=client)
        self.assertNotIn("chave-ficticia", str(caught.exception))
        self.assertNotIn("conteudo-privado", str(caught.exception))

    def test_transient_503_is_retried_then_succeeds(self):
        calls = []
        def handler(request):
            calls.append(1)
            if len(calls) < 3:
                return httpx.Response(503, json={"error": {"message": "high demand"}})
            return httpx.Response(200, json={"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": "ok"}]}}]})
        with patch("alertagolpe.providers.time.sleep") as sleep:
            result = generate("s", "p", ProviderConfig("gemini", "modelo", "chave-ficticia"), client=self.client(handler))
        self.assertEqual(result.text, "ok")
        self.assertEqual(len(calls), 3)
        self.assertEqual(sleep.call_count, 2)

    def test_persistent_503_gives_up_after_limited_retries(self):
        calls = []
        def handler(request):
            calls.append(1)
            return httpx.Response(503, text="conteudo-privado")
        with patch("alertagolpe.providers.time.sleep") as sleep:
            with self.assertRaises(ProviderError) as caught:
                generate("s", "p", ProviderConfig("gemini", "modelo", "chave-ficticia"), client=self.client(handler))
        self.assertEqual(len(calls), 4)
        self.assertEqual(sleep.call_count, 3)
        self.assertIn("503", str(caught.exception))
        self.assertNotIn("conteudo-privado", str(caught.exception))

    def test_timeout_is_retried_once(self):
        calls = []
        def flaky(request):
            calls.append(1)
            if len(calls) == 1:
                raise httpx.ReadTimeout("lento")
            return httpx.Response(200, json={"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": "ok"}]}}]})
        self.assertEqual(generate("s", "p", ProviderConfig("gemini", "modelo", "chave-ficticia"), client=self.client(flaky)).text, "ok")
        self.assertEqual(len(calls), 2)
        calls.clear()
        def stuck(request):
            calls.append(1)
            raise httpx.ReadTimeout("lento")
        with self.assertRaises(ProviderError):
            generate("s", "p", ProviderConfig("gemini", "modelo", "chave-ficticia"), client=self.client(stuck))
        self.assertEqual(len(calls), 2)

    def test_errors_flag_when_another_model_could_work(self):
        cases = {503: True, 500: True, 404: True, 429: True, 401: False, 403: False, 400: False}
        for status, expected in cases.items():
            with self.subTest(status=status), patch("alertagolpe.providers.time.sleep"):
                with self.assertRaises(ProviderError) as caught:
                    generate("s", "p", ProviderConfig("gemini", "modelo", "chave-ficticia"), client=self.client(lambda r, st=status: httpx.Response(st)))
                self.assertEqual(caught.exception.model_unavailable, expected)
        def slow(request):
            raise httpx.ReadTimeout("lento")
        with self.assertRaises(ProviderError) as caught:
            generate("s", "p", ProviderConfig("gemini", "modelo", "chave-ficticia"), client=self.client(slow))
        self.assertTrue(caught.exception.model_unavailable)

    def test_quota_and_auth_errors_are_not_retried(self):
        for status in (400, 401, 403, 404, 429):
            with self.subTest(status=status):
                calls = []
                def handler(request):
                    calls.append(1)
                    return httpx.Response(status)
                with patch("alertagolpe.providers.time.sleep") as sleep:
                    with self.assertRaises(ProviderError):
                        generate("s", "p", ProviderConfig("gemini", "modelo", "chave-ficticia"), client=self.client(handler))
                self.assertEqual(len(calls), 1)
                sleep.assert_not_called()

    def test_retry_after_header_is_respected_with_cap(self):
        from alertagolpe.providers import MAX_RETRY_AFTER, _retry_delay
        self.assertGreaterEqual(_retry_delay(httpx.Response(503, headers={"retry-after": "8"}), 0), 8)
        self.assertLessEqual(_retry_delay(httpx.Response(503, headers={"retry-after": "999"}), 0), MAX_RETRY_AFTER + 0.5)

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

    @patch("alertagolpe.providers.httpx.Client")
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

    @patch("alertagolpe.providers.httpx.Client")
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
