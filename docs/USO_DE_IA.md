# Registro de assistência de IA e contribuições

O enunciado exige que o uso de IA seja explicitamente descrito e contextualizado,
inclusive na escrita dos materiais. Este registro acompanha o desenvolvimento do
AlertaGolpe e é resumido no relatório e na apresentação.

## Assistência registrada

| Data | Ferramenta/modelo | Finalidade | Arquivos | Revisor | Evidência |
| --- | --- | --- | --- | --- | --- |
| 16–17/11/2026 | Codex (OpenAI) | Módulos de base: cliente HTTP da API Gemini com novas tentativas, busca TF-IDF com similaridade do cosseno e leitura de configuração pelo `.env` | `providers.py`, `retrieval.py`, `settings.py` e respectivos testes | Gustavo Henrique Leão | Testes automatizados dos módulos; a chave da API fica só no `.env` privado |
| 17/11/2026 | Claude Code (Claude Opus 5.5) | Catálogo de 16 golpes a partir de fontes públicas; regras locais; análise com Gemini (modo JSON e validação de trechos); interface com tema de alerta; conjunto de avaliação fictício (20 golpes, 12 legítimas) e script `avaliar.py`; redação do relatório e geração do Word/PDF | `src/alertagolpe/`, `tests/`, `avaliacao/`, `avaliar.py`, `assets/styles.css`, `README.md`, `docs/RELATORIO.md` | Gustavo Henrique Leão | 54 testes automatizados; avaliação real com `gemini-3.5-flash-lite` em 17/11: regras 21/32, regras + catálogo + IA 32/32 (após nova tentativa para 2 respostas com JSON inválido) |
| 18/11/2026 | Claude Code (Claude Opus 5.5) | Modelos reserva automáticos; correção de alarme falso em mensagem real do Nubank (o modelo afirmou que o telefone oficial era falso e citou link inexistente): regras de honestidade e sinais de legitimidade no prompt (versão alertagolpe-v2), regra local de canal oficial, temperatura 0, até 3 tentativas para JSON inválido, 429 acionando modelo reserva, limite de mensagem de 10 mil caracteres; conjunto ampliado para 36 mensagens; slides da apresentação | `src/alertagolpe/`, `tests/`, `avaliacao/mensagens.json`, `README.md`, `docs/RELATORIO.md` | Gustavo Henrique Leão | 56 testes automatizados; avaliação final em 18/11: regras 24/36, regras + catálogo + IA 36/36; casos sensíveis estáveis em 5 de 5 execuções; resultado em `output/avaliacao-resultados.json` |
| Em uso | Gemini (`gemini-3.5-flash-lite`; reservas `gemini-3.1-flash-lite` e `gemini-flash-lite-latest`) | Modelo generativo do aplicativo: recebe a mensagem, os sinais das regras e os 3 golpes mais parecidos do catálogo | `src/alertagolpe/analyzer.py` | — | Modelo usado registrado em cada análise e no resultado da avaliação |

Para chamadas do aplicativo, registrar provedor, identificador do modelo,
parâmetros relevantes, data e finalidade. Não armazenar credenciais nem
conteúdo pessoal. O texto de uma resposta simulada não comprova uma chamada real.

## Participação do grupo

O desenvolvimento do código foi concentrado em Gustavo Henrique Leão, com
assistência de IA. As demais atividades foram divididas entre os integrantes:

| Integrante | Atividades |
| --- | --- |
| Gustavo Henrique Leão | Coordenação; desenvolvimento da aplicação com assistência do Codex e do Claude Code; integração com a API Gemini; testes com mensagens reais (incluindo o alarme falso da seção 4.1 do relatório); revisão do código, do catálogo, da avaliação e do relatório |
| Otavio Aparecido Pegorin | Conferência do catálogo de golpes com as fontes da Febraban e do Banco Central; testes com novas mensagens reais |
| Leonardo Gabriel Lopes | Demonstração ao vivo da aplicação na apresentação e preparação do ambiente, com plano alternativo |
| Felipe Gabriel Tagliabues | Vídeo tutorial da Parte 2 (roteiro e gravação) |
| Murilo Rodrigues Lima | Slides e ensaio da apresentação oral (divisão das falas e preparação para as perguntas) |

## Declaração

> Utilizamos assistência de IA nas atividades descritas neste registro. O código
> e os textos gerados foram revisados por Gustavo Henrique Leão, e as decisões
> humanas e limitações observadas estão documentadas no relatório. No
> aplicativo, o modelo generativo recebe a mensagem colada pelo usuário, os
> sinais das regras locais e os golpes mais parecidos do catálogo. Os
> integrantes realizaram as atividades de gravação, edição e apresentação
> indicadas acima.

## Cuidados para a entrega

- O nome e a versão do modelo devem corresponder ao que foi executado.
- Mostrar sinais e trechos não garante que a classificação esteja correta.
- Resultados, custos e tempos somente quando observados ou medidos.
- Chaves e mensagens pessoais ficam fora do pacote e das gravações.
- Gravação e edição precisam ser realizadas pelos integrantes, conforme o enunciado.

## Referências

- API Gemini: https://ai.google.dev/gemini-api/docs
- Documentação de cada biblioteca: consultar os links em RELATORIO.md.
