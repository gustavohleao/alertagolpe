"""Testes de cobertura documental e limites, sem chamadas a modelos reais."""

from dataclasses import replace
import json
import unittest
from unittest.mock import patch

from estudapdf.document import Page
from estudapdf.providers import Generation, ProviderConfig, ProviderError
from estudapdf.summary import (
    MAX_CALLS,
    MAX_FINAL_BYTES,
    MAX_NOTE_BYTES,
    MAX_PROMPT_BYTES,
    SYSTEM_PROMPT,
    SummaryError,
    prepare_summary,
    summarize,
)


class SummaryTests(unittest.TestCase):
    def setUp(self):
        self.config = ProviderConfig("gemini", "modelo-teste", "chave-secreta-de-teste")

    @staticmethod
    def small_generation(system, prompt, config):
        data = json.loads(prompt)
        if "fontes" in data:
            ids = [item["id"] for item in data["fontes"]]
        else:
            from re import findall
            ids = list(dict.fromkeys(findall(r"P\d+-R\d+", " ".join(item["texto"] for item in data["notas"]))))
        return Generation("Conceitos centrais do texto. " + " ".join(f"[{source_id}]" for source_id in ids), config.model, 0.01, {"totalTokenCount": 10})

    def test_plan_has_independent_ids_and_preserves_original_pages(self):
        plan = prepare_summary([Page(3, "Aprendizado supervisionado usa rótulos."), Page(8, "RAG recupera fontes.", "Seção")])
        self.assertEqual(plan.pages, (3, 8))
        self.assertEqual([chunk.id for chunk in plan.source_chunks], ["P3-R1", "P8-R1"])
        self.assertEqual(plan.source_chunks[1].location_label, "Seção")
        self.assertEqual(plan.max_calls, 2 * len(plan.blocks) - 1)

    @patch("estudapdf.summary.generate")
    def test_every_segment_and_last_page_are_sent_without_deduplication(self, generate):
        pages = [Page(1, "mesmo conteúdo " * 400), Page(2, "mesmo conteúdo " * 400), Page(9, "MARCADOR ULTIMA PAGINA")]
        plan = prepare_summary(pages)
        generate.side_effect = self.small_generation
        result = summarize(plan, self.config, allow_external=True)
        sent_sources = [source for call in generate.call_args_list for source in json.loads(call.args[1]).get("fontes", [])]
        self.assertEqual([item["id"] for item in sent_sources], [chunk.id for chunk in plan.source_chunks])
        self.assertEqual([item["texto"] for item in sent_sources], [chunk.text for chunk in plan.source_chunks])
        self.assertTrue(any("MARCADOR ULTIMA PAGINA" in item["texto"] for item in sent_sources))
        self.assertIn(2, result.pages)
        self.assertEqual(result.characters, sum(len(page.text) for page in pages))

    def test_long_single_page_is_split_without_overlap_or_loss(self):
        text = "abcdefghijklmnopqrstuvwxyz" * 180
        plan = prepare_summary([Page(12, text)])
        self.assertEqual("".join(chunk.text for chunk in plan.source_chunks), text)
        self.assertTrue(all(len(chunk.text) <= 1000 for chunk in plan.source_chunks))
        self.assertTrue(all(chunk.id.startswith("P12-R") for chunk in plan.source_chunks))

    @patch("estudapdf.summary.generate")
    def test_missing_external_consent_makes_zero_calls(self, generate):
        plan = prepare_summary([Page(1, "Texto autorizado para leitura local.")])
        with self.assertRaisesRegex(SummaryError, "0 chamada.*Autorize"):
            summarize(plan, self.config)
        generate.assert_not_called()

    @patch("estudapdf.summary.generate")
    def test_local_provider_is_rejected(self, generate):
        with self.assertRaises(SummaryError):
            summarize(prepare_summary([Page(1, "Texto do material.")]), ProviderConfig("ollama", "modelo-local"))
        generate.assert_not_called()

    @patch("estudapdf.summary.generate")
    def test_invalid_inputs_and_plan_budget_fail_before_network(self, generate):
        for pages in ([], [Page(1, " ")], [Page(1, "x" * 60_001)], [Page(2, "texto"), Page(2, "outro")]):
            with self.subTest(pages_count=len(pages)), self.assertRaises(SummaryError):
                prepare_summary(pages)
        # The byte budget makes this input exceed the call budget before the
        # absolute character cap: it must fail instead of taking a prefix.
        with self.assertRaisesRegex(SummaryError, "chamadas"):
            prepare_summary([Page(1, "漢" * 40_000)])
        plan = prepare_summary([Page(1, "Conceitos.")])
        with self.assertRaises(SummaryError):
            summarize(replace(plan, max_calls=MAX_CALLS + 1), self.config, allow_external=True)
        generate.assert_not_called()

    @patch("estudapdf.summary.generate")
    def test_complete_serialized_prompts_respect_utf8_budget(self, generate):
        plan = prepare_summary([Page(1, "ação e atenção " * 600)])
        generate.side_effect = self.small_generation
        result = summarize(plan, self.config, allow_external=True)
        for call in generate.call_args_list:
            system, prompt = call.args[:2]
            self.assertEqual(system, SYSTEM_PROMPT)
            self.assertLessEqual(len((system + "\n" + prompt).encode("utf-8")), MAX_PROMPT_BYTES)
        self.assertTrue(all(record["bytes_prompt_completo"] <= MAX_PROMPT_BYTES for record in result.records))

    @patch("estudapdf.summary.generate")
    def test_hierarchical_reduction_and_progress_fit_call_budget(self, generate):
        plan = prepare_summary([Page(page, ("Conteúdo importante e contexto. " * 155)) for page in range(1, 7)])

        def long_valid_note(system, prompt, config):
            short = self.small_generation(system, prompt, config)
            data = json.loads(prompt)
            final = data["etapa"] in {"resumo_final", "sintese_final"}
            # Large but valid notes force multiple synthesis levels.
            limit = 1350 if final else 1650
            text = short.text + " " + "detalhe " * max(0, (limit - len(short.text.encode("utf-8"))) // 8)
            return Generation(text, config.model, 0.01, {})

        generate.side_effect = long_valid_note
        progress = []
        result = summarize(plan, self.config, allow_external=True, on_progress=lambda *args: progress.append(args))
        stages = [json.loads(call.args[1])["etapa"] for call in generate.call_args_list]
        self.assertIn("sintese_intermediaria", stages)
        self.assertEqual(stages[-1], "sintese_final")
        self.assertLessEqual(result.calls_completed, plan.max_calls)
        self.assertLessEqual(result.calls_completed, MAX_CALLS)
        self.assertEqual(progress[0][0], 0)
        self.assertEqual(progress[-1][0], result.calls_completed)
        self.assertTrue(all(item[1] == plan.max_calls for item in progress))
        self.assertTrue(set(result.citations).issubset({chunk.id for chunk in plan.source_chunks}))

    @patch("estudapdf.summary.generate")
    def test_unknown_empty_and_refusal_outputs_are_rejected(self, generate):
        plan = prepare_summary([Page(1, "Aprendizado usa exemplos.")])
        outputs = [
            "", "Resumo [P999-R1].", "Resumo [P1-T1].",
            "Resumo [P1-R1] e [P9-X2].",
            "Não encontrei informação suficiente no material. [P1-R1]",
        ]
        for output in outputs:
            generate.reset_mock()
            generate.return_value = Generation(output, "modelo", 0.01, {})
            with self.subTest(output=output), self.assertRaisesRegex(SummaryError, "1 chamada"):
                summarize(plan, self.config, allow_external=True)

    @patch("estudapdf.summary.generate")
    def test_final_single_block_without_citations_has_warning_and_no_invented_ids(self, generate):
        plan = prepare_summary([Page(1, "Aprendizado usa exemplos.")])
        generate.return_value = Generation("O material explica o aprendizado a partir de exemplos.", "modelo", 0.01, {})
        result = summarize(plan, self.config, allow_external=True)
        self.assertEqual(result.citations, ())
        self.assertIn("O modelo não indicou referências", result.warning)
        self.assertIn("não comprovam", result.warning)
        self.assertNotIn("P1-R1", result.text)
        self.assertEqual(result.source_chunks, plan.source_chunks)
        self.assertEqual(result.export("fonte.pdf")["warning"], result.warning)
        self.assertEqual(result.calls_completed, 1)

    @patch("estudapdf.summary.generate")
    def test_final_reduction_without_citations_has_warning(self, generate):
        plan = prepare_summary([Page(1, "x" * 10_000)])
        self.assertGreater(len(plan.blocks), 1)

        def handler(system, prompt, config):
            data = json.loads(prompt)
            if "fontes" in data:
                return self.small_generation(system, prompt, config)
            self.assertEqual(data["etapa"], "sintese_final")
            return Generation("Síntese dos conceitos apresentados em todas as partes.", config.model, 0.01, {})

        generate.side_effect = handler
        result = summarize(plan, self.config, allow_external=True)
        self.assertEqual(result.citations, ())
        self.assertIn("O modelo não indicou referências", result.warning)
        self.assertEqual(result.calls_completed, len(plan.blocks) + 1)

    @patch("estudapdf.summary.generate")
    def test_partial_map_without_citations_still_fails(self, generate):
        plan = prepare_summary([Page(1, "x" * 10_000)])
        generate.return_value = Generation("Uma nota parcial sem referências.", "modelo", 0.01, {})
        with self.assertRaisesRegex(SummaryError, "1 chamada.*não contém referências"):
            summarize(plan, self.config, allow_external=True)
        self.assertEqual(generate.call_count, 1)

    @patch("estudapdf.summary.generate")
    def test_intermediate_reduction_without_citations_still_fails(self, generate):
        plan = prepare_summary([Page(page, "Conteúdo importante e contexto. " * 155) for page in range(1, 7)])

        def handler(system, prompt, config):
            data = json.loads(prompt)
            if "fontes" in data:
                text = f"Conceitos [{data['fontes'][0]['id']}]. " + "detalhe " * 195
                return Generation(text, config.model, 0.01, {})
            self.assertEqual(data["etapa"], "sintese_intermediaria")
            return Generation("Uma síntese intermediária sem referências.", config.model, 0.01, {})

        generate.side_effect = handler
        with self.assertRaisesRegex(SummaryError, "não contém referências"):
            summarize(plan, self.config, allow_external=True)
        self.assertEqual(generate.call_count, len(plan.blocks) + 1)

    @patch("estudapdf.summary.generate")
    def test_utf8_output_limit_is_bytes_not_characters(self, generate):
        plan = prepare_summary([Page(1, "Conceitos do texto.")])
        # Less than 4000 characters but more than 4000 bytes.
        generate.return_value = Generation("漢" * 1400 + " [P1-R1]", "modelo", 0.01, {})
        with self.assertRaisesRegex(SummaryError, str(MAX_FINAL_BYTES)):
            summarize(plan, self.config, allow_external=True)

    @patch("estudapdf.summary.generate")
    def test_partial_note_limit_rejects_without_truncation(self, generate):
        plan = prepare_summary([Page(1, "x" * 10_000)])
        first_id = plan.blocks[0][0].id
        generate.return_value = Generation("a" * MAX_NOTE_BYTES + f" [{first_id}]", "modelo", 0.01, {})
        with self.assertRaisesRegex(SummaryError, str(MAX_NOTE_BYTES)):
            summarize(plan, self.config, allow_external=True)
        self.assertEqual(generate.call_count, 1)

    @patch("estudapdf.summary.generate")
    def test_map_cannot_cite_another_branch(self, generate):
        plan = prepare_summary([Page(1, "x" * 10_000)])
        unrelated_id = plan.blocks[-1][-1].id
        self.assertNotIn(unrelated_id, {chunk.id for chunk in plan.blocks[0]})
        generate.return_value = Generation(f"Resumo [{unrelated_id}].", "modelo", 0.01, {})
        with self.assertRaisesRegex(SummaryError, "não foi fornecida nesta etapa"):
            summarize(plan, self.config, allow_external=True)
        self.assertEqual(generate.call_count, 1)

    @patch("estudapdf.summary.generate")
    def test_reduction_cannot_restore_a_source_not_cited_by_its_inputs(self, generate):
        plan = prepare_summary([Page(1, "x" * 10_000)])
        hidden_id = plan.blocks[0][-1].id
        self.assertNotEqual(hidden_id, plan.blocks[0][0].id)

        def handler(system, prompt, config):
            data = json.loads(prompt)
            source_id = data["fontes"][0]["id"] if "fontes" in data else hidden_id
            return Generation(f"Resumo [{source_id}].", config.model, 0.01, {})

        generate.side_effect = handler
        with self.assertRaisesRegex(SummaryError, "não foi fornecida nesta etapa"):
            summarize(plan, self.config, allow_external=True)

    @patch("estudapdf.summary.generate")
    def test_intermediate_reduction_cannot_cite_another_branch(self, generate):
        plan = prepare_summary([Page(page, "Conteúdo importante e contexto. " * 155) for page in range(1, 7)])
        unrelated_id = plan.blocks[-1][0].id

        def handler(system, prompt, config):
            data = json.loads(prompt)
            if "fontes" in data:
                text = f"Conceitos [{data['fontes'][0]['id']}]. " + "detalhe " * 195
            else:
                self.assertNotIn(unrelated_id, " ".join(item["texto"] for item in data["notas"]))
                text = f"Síntese [{unrelated_id}]."
            return Generation(text, config.model, 0.01, {})

        generate.side_effect = handler
        with self.assertRaisesRegex(SummaryError, "não foi fornecida nesta etapa"):
            summarize(plan, self.config, allow_external=True)
        self.assertEqual(generate.call_count, len(plan.blocks) + 1)

    @patch("estudapdf.summary.generate")
    def test_pair_of_notes_exceeding_serialized_budget_is_not_truncated(self, generate):
        plan = prepare_summary([Page(1, "x" * 6000)])
        self.assertGreater(len(plan.blocks), 1)

        def handler(system, prompt, config):
            data = json.loads(prompt)
            self.assertIn("fontes", data)
            # A note fits 1800 raw bytes, but JSON escaping doubles each slash.
            # The pair therefore cannot fit its complete 6000-byte prompt.
            return Generation("\\" * 1700 + f" [{data['fontes'][0]['id']}]", config.model, 0.01, {})

        generate.side_effect = handler
        with self.assertRaisesRegex(SummaryError, "Duas notas não cabem"):
            summarize(plan, self.config, allow_external=True)
        self.assertEqual(generate.call_count, len(plan.blocks))

    @patch("estudapdf.summary.generate")
    def test_timeout_after_first_map_has_no_partial_success_result(self, generate):
        plan = prepare_summary([Page(1, "x" * 10_000)])
        first_id = plan.blocks[0][0].id
        generate.side_effect = [Generation(f"Primeira nota [{first_id}].", "modelo", 0.01, {}), ProviderError("Tempo de espera excedido.")]
        with self.assertRaisesRegex(SummaryError, "1 chamada.*Tempo de espera.*Nenhum resultado parcial"):
            summarize(plan, self.config, allow_external=True)
        self.assertEqual(generate.call_count, 2)

    @patch("estudapdf.summary.generate")
    def test_export_has_prompts_and_sources_but_never_config_key(self, generate):
        generate.side_effect = self.small_generation
        result = summarize(prepare_summary([Page(1, "RAG usa fontes.")]), self.config, allow_external=True)
        exported = result.export("apostila.pdf")
        text = json.dumps(exported, ensure_ascii=False)
        self.assertNotIn(self.config.api_key, text)
        self.assertIn(SYSTEM_PROMPT, result.records[0]["sistema"])
        self.assertEqual(exported["fonte"], "apostila.pdf")
        self.assertEqual(exported["calls_completed"], 1)
        self.assertEqual(result.citations, ("P1-R1",))
        self.assertEqual(result.warning, "")


if __name__ == "__main__":
    unittest.main()
