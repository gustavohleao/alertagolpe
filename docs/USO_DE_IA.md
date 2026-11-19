# Registro de assistência de IA e contribuições

O enunciado exige que o uso de IA seja explicitamente descrito e contextualizado,
inclusive na escrita dos materiais. Este registro acompanha o desenvolvimento do
AlertaGolpe e é resumido no relatório e na apresentação.

## Assistência registrada

| Data | Ferramenta/modelo | Finalidade | Arquivos | Revisor | Evidência |
| --- | --- | --- | --- | --- | --- |
| 16–17/11/2026 | Codex (OpenAI) | Módulos de base: cliente HTTP da API Gemini com novas tentativas, busca TF-IDF com similaridade do cosseno e leitura de configuração pelo `.env` | `providers.py`, `retrieval.py`, `settings.py` e respectivos testes | Gustavo Henrique Leão | Testes automatizados dos módulos; a chave da API fica só no `.env` privado |
| 17/11/2026 | Claude Code (Claude Opus 5.5) | Catálogo de 16 golpes (17 após o caso do MEI) a partir de fontes públicas; regras locais; análise com Gemini (modo JSON e validação de trechos); interface com tema de alerta; conjunto de avaliação fictício (20 golpes, 12 legítimas) e script `avaliar.py`; redação do relatório e geração do Word/PDF | `src/alertagolpe/`, `tests/`, `avaliacao/`, `avaliar.py`, `assets/styles.css`, `README.md`, `docs/RELATORIO.md` | Gustavo Henrique Leão | 54 testes automatizados; avaliação real com `gemini-3.5-flash-lite` em 17/11: regras 21/32, regras + catálogo + IA 32/32 (após nova tentativa para 2 respostas com JSON inválido) |
| 18/11/2026 | Claude Code (Claude Opus 5.5) | Modelos reserva automáticos; correção de alarme falso em mensagem real do Nubank (o modelo afirmou que o telefone oficial era falso e citou link inexistente): regras de honestidade e sinais de legitimidade no prompt (versão alertagolpe-v2), regra local de canal oficial, temperatura 0, até 3 tentativas para JSON inválido, 429 acionando modelo reserva, limite de mensagem de 10 mil caracteres; conjunto ampliado para 36 mensagens; slides da apresentação; depois de um e-mail real de falsa regularização do MEI receber só risco médio: golpe G17 no catálogo (fontes Sebrae e gov.br), regra local de pendência, prompt alertagolpe-v3 e conjunto com 38 mensagens | `src/alertagolpe/`, `tests/`, `avaliacao/mensagens.json`, `README.md`, `docs/RELATORIO.md` | Gustavo Henrique Leão | 56 testes automatizados; avaliação final em 18/11: regras 26/38, regras + catálogo + IA 38/38 (23/23 golpes como risco alto); depois, testes com 76 mensagens inéditas escritas com assistência de IA (56 de ajuste e 20 de reserva, 76/76 no risco), 4 golpes novos no catálogo (G18 a G21, com fontes) e conjunto principal com 45 mensagens: regras 29/45, regras + catálogo + IA 45/45; normalização de texto disfarçado nas regras e prompt alertagolpe-v4 (teste de escrita fora do padrão: 13/14 → 14/14); um agente de pesquisa do Claude Code abriu cerca de 130 páginas públicas e copiou 34 mensagens reais com a fonte (parte conferida manualmente), divididas em 18 para o catálogo (`exemplos_reais.json`) e 16 para teste (16/16 detectadas; tipo de golpe 10/14 → 11/14); em 19/11, 9 golpes novos (G22 a G30, com fontes), diagnóstico de mudança de comportamento do Gemini e prompt alertagolpe-v5 com regra de calibragem; avaliação final: principal 55/55 (+1 falha do serviço), reserva 20/20, reais 15/16; casos sensíveis estáveis em 5 de 5 execuções; resultado em `output/avaliacao-resultados.json` |
| 19/11/2026 | Claude Code (Claude Opus 5.5) | Suporte a LLM local pelo Ollama (`qwen2.5:3b`, já instalado no notebook do grupo): cliente HTTP restrito a `localhost`, troca automática para o modelo local sem internet, opção `LLM_PROVIDER=ollama`, avaliação com `--provedor ollama`; atualização de relatório, README e diagramas | `src/alertagolpe/providers.py`, `analyzer.py`, `frontend.py`, `settings.py`, `avaliar.py`, `tests/`, `docs/RELATORIO.md`, `README.md` | Gustavo Henrique Leão | 63 testes automatizados; avaliação real do Qwen nas 16 mensagens reais de teste: 14/14 golpes detectados, 2/2 alarmes falsos (marcou tudo como risco alto), 153 s por mensagem em média; mantido só como reserva |
| Em uso | Gemini (`gemini-3.5-flash-lite`; reservas `gemini-3.1-flash-lite` e `gemini-flash-lite-latest`) e, como reserva local, Qwen 2.5 3B via Ollama (`qwen2.5:3b`) | Modelo generativo do aplicativo: recebe a mensagem, os sinais das regras e os 3 golpes mais parecidos do catálogo | `src/alertagolpe/analyzer.py` | — | Modelo usado registrado em cada análise e no resultado da avaliação |

Para chamadas do aplicativo, registrar provedor, identificador do modelo,
parâmetros relevantes, data e finalidade. Não armazenar credenciais nem
conteúdo pessoal. O texto de uma resposta simulada não comprova uma chamada real.

## Participação do grupo

O desenvolvimento do código foi concentrado em Gustavo Henrique Leão, com
assistência de IA.

## Declaração

> Utilizamos assistência de IA nas atividades descritas neste registro. O código
> e os textos gerados foram revisados por Gustavo Henrique Leão, e as decisões
> humanas e limitações observadas estão documentadas no relatório. No
> aplicativo, o modelo generativo recebe a mensagem colada pelo usuário, os
> sinais das regras locais e os golpes mais parecidos do catálogo. A gravação
> e a edição do vídeo e a apresentação foram feitas pelos integrantes do grupo.

## Cuidados para a entrega

- O nome e a versão do modelo devem corresponder ao que foi executado.
- Mostrar sinais e trechos não garante que a classificação esteja correta.
- Resultados, custos e tempos somente quando observados ou medidos.
- Chaves e mensagens pessoais ficam fora do pacote e das gravações.
- Gravação e edição precisam ser realizadas pelos integrantes, conforme o enunciado.

## Referências

- API Gemini: https://ai.google.dev/gemini-api/docs
- Ollama: https://github.com/ollama/ollama/blob/main/docs/api.md
- Documentação de cada biblioteca: consultar os links em RELATORIO.md.
