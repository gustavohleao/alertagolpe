# Registro de assistência de IA e contribuições

O enunciado exige que o uso de IA seja explicitamente descrito e contextualizado,
inclusive na escrita dos materiais. Este registro deve acompanhar o desenvolvimento
e ser resumido no relatório e na apresentação.

## Assistência já registrada

| Data | Ferramenta | Atividade | Situação e revisão |
| --- | --- | --- | --- |
| 16/11/2026 | Codex | Discussão do escopo, proposta EstudaPDF com RAG e planejamento da entrega | O usuário esclareceu que pertence a um grupo, mas concentra a execução |
| 16/11/2026 | Codex | Elaboração de rascunhos de relatório, roteiro, conteúdo de slides e plano em Markdown | Revisão humana e adequação à implementação final pendentes |
| 16/11/2026 | Codex | Assistência na implementação e registro de testes: 35 testes passaram e servidor respondeu HTTP 200 | 17 núcleo, sete provedores, sete serviço, quatro interface; HTTP dos testes simulado; conferência humana pendente |
| 16/11/2026 | Codex | Demo interna textual com autoria assistida por IA e avaliação exploratória da recuperação | Seção esperada no top 3 em 8/8 positivas; dez casos, duas sem resposta fora da contagem; não é PDF nem avaliação independente |
| 16/11/2026 | Ollama local | Consulta real do serviço em 127.0.0.1:11434 e listagem de modelos | llama3.2:1b e qwen2.5:3b disponíveis |
| 16/11/2026 | Ollama / qwen2.5:3b | Geração real para “Como funciona a geração aumentada por recuperação RAG?” com contexto da demo | Concluída em 133,11 s; timeout local 180 s; registro output/validacao-ollama.json |
| 16/11/2026 | Codex | Conferência assistida por IA da resposta real | Definição e etapas coerentes com seção 2; referência [P2-T1] existente; não houve revisão humana registrada |
| 16/11/2026 | Ollama / llama3.2:1b | Segunda execução real da mesma pergunta sobre RAG | 25,081 s; respondeu que não encontrou informação suficiente, apesar da seção 2; registro output/validacao-ollama-1b.json |
| 16/11/2026 | Codex | Conferência assistida por IA da segunda execução | Recusa indevida; piloto não controlado com diferenças de ordem/cache e pequenas diferenças de formatação; não demonstra efeito isolado do tamanho do modelo |
| 16/11/2026 | Codex | Adaptação do tutorial para Ollama e atualização do estado documental | Vídeo ainda não gravado/editado; PDF real e revisão humana pendentes |
| 17/11/2026 | Codex | Assistência na implementação do novo fluxo de resumo global e atualização dos cinco materiais em Markdown | summary.py implementado; revisão humana pendente |
| 17/11/2026 | Ollama / qwen2.5:3b | Dois pilotos reais de resumo | HTTP concluído; saída rejeitada por falta de IDs; registros output/validacao-resumo-ollama.json e output/validacao-resumo-ollama-v2.json; texto bruto não preservado |
| 17/11/2026 | Codex | Registro de testes e ajuste da política de referências finais | Fase inicial com 56 testes; após o ajuste, 61 passaram: 35 anteriores, 21 resumo e cinco interface; HTTP dos testes simulado |
| 17/11/2026 | Ollama / qwen2.5:3b | Terceiro piloto real de resumo | Concluído em 99,018 s; quatro seções/3.312 caracteres, um mapa/uma chamada, sem IDs e com warning; output/validacao-resumo-ollama-v3.json |
| 17/11/2026 | Codex | Revisão assistida por IA do terceiro piloto | Aborda os quatro temas, mas abertura pode confundir tarefas supervisionadas e não supervisionadas; não é aprovação humana ou qualidade geral validada |
| 17/11/2026 | Codex | Conferência headless desktop/móvel da nova aba | Plano de quatro seções/3.312 caracteres/até uma chamada; intervalo 1–2 atualizou para duas seções/1.612 caracteres; nenhuma chamada ao modelo durante essa conferência |

Complementar este registro conforme novos testes ocorrerem. Gemini permanece
opcional, sem geração real validada neste registro. Duas execuções reais de perguntas no Ollama
foram registradas separadamente dos testes com HTTP simulado. qwen2.5:3b permanece
na configuração local. Não registrar como concluídos prompts, gerações ou revisões
ainda não realizados. Uma pergunta da demo textual, executada com dois modelos,
não valida PDF real ou qualidade geral das respostas.

## Registro das próximas atividades

Atualização de configuração em 17/11/2026: Codex auxiliou na remoção do campo
de chave/senha da interface e na centralização da configuração do servidor,
conforme solicitação do usuário. `GEMINI_API_KEY` passa a ser carregada do
`.env` privado ou do ambiente do processo; nenhuma chave deve ser embutida em
fonte compartilhável. A interface mostra somente definida/ausente, preservando
as opções de provedor/modelo. Para Gemini, configurar `LLM_PROVIDER=gemini`;
`LLM_MODEL` é opcional até listar e escolher um modelo. O arquivo é relido a
cada reexecução depois de atualizar a página, sem reiniciar o servidor; valores
explícitos do ambiente do processo têm prioridade. Os consentimentos de
pergunta e resumo permanecem. Esta atualização não registra uso de segredo
real nem nova autenticação. A suíte final teve 76 testes aprovados: os 65
anteriores, oito da configuração e três da interface com chave no servidor.
Os resultados históricos abaixo permanecem preservados.

Atualização técnica de 17/11/2026: Codex diagnosticou o bloqueio de acesso à
API Gemini no processo de desenvolvimento (WinError 10013), reiniciou o app
com rede permitida e corrigiu a normalização da chave. A suíte passou a 65
testes. Houve sondagens ao endpoint oficial sem chave real e uma consulta
com chave fictícia, sem documentos ou geração. Isso não valida uma conta
Gemini nem comprova qualidade de respostas desse provedor.

Atualização de 17/11/2026: Codex auxiliou no redesenho do frontend solicitado
pelo usuário: identidade visual, layout responsivo, painel de fontes e
organização das configurações. A interface foi separada em `frontend.py`,
`ui.py` e `assets/styles.css`, preservando o backend e a autorização de envio.
Os 35 testes automatizados passaram após a refatoração. A revisão humana do
visual e dos materiais continua necessária.

Em 17/11, o usuário solicitou resumir o material. O fluxo de resumo foi
implementado e se distingue das perguntas: usa todo o texto extraído de um
intervalo por mapa e síntese, enquanto o RAG usa até três trechos relevantes.
O planejamento verifica 60 mil caracteres, até 20 chamadas previstas e orçamento
heurístico de 6 mil bytes UTF-8 por prompt; excesso exige intervalo menor,
sem corte silencioso. As referências de resumo, como `[P12-R1]`, devem preservar
a origem e são distintas de `[P12-T1]` no RAG. Notas intermediárias exigem IDs
originais. A política implementada permite saída final sem IDs com aviso explícito
e origens chamadas “Texto processado”, sem atribuir citações não emitidas.
TXT inclui o aviso e JSON inclui `warning`. IDs desconhecidos, saída vazia,
recusa sem resumo, saída longa e demais falhas continuam rejeitados.

Gemini requer autorização específica para enviar todo o texto extraído do
intervalo, separada da pergunta. O modo somente busca não realiza resumo.
O resultado e o material permanecem em memória de sessão; exportações TXT e
JSON não devem incluir chaves, mas podem conter conteúdo documental. Falhas
não devem apresentar um resumo parcial como completo. Cobertura, omissões e
extração de imagens/tabelas precisam ser discutidas e conferidas por humanos.

Os 35 testes e as duas gerações reais de perguntas registrados em 16/11 não
validam o resumo. Em 17/11, dois pilotos reais de resumo tiveram a saída rejeitada
por ausência de IDs; os textos brutos não foram preservados e não permitem
afirmar qualidade correta ou incorreta. A suíte final com 61 testes passou
depois do ajuste. O terceiro piloto concluiu com aviso e preservou o texto;
a revisão assistida por IA identificou uma ambiguidade na primeira frase.
Uma execução de uma chamada não valida síntese em múltiplas chamadas, PDF
real ou qualidade geral. Revisão humana e vídeo continuam pendentes. Nenhum
novo teste real de Gemini foi realizado.

| Data | Ferramenta/modelo real | Finalidade e entrada resumida | Saída ou arquivo | Revisor e alterações | Evidência de execução |
| --- | --- | --- | --- | --- | --- |
| 17/11/2026 | Claude Code (Claude Opus 5.5) | Redesenho visual da interface; biblioteca de materiais da sessão na barra lateral e envio de PDF no centro; remoção das caixas de autorização a pedido do usuário; diagnóstico da chave Gemini (troca de `LLM_MODEL` para `gemini-3.5-flash-lite` após erro 503 em `gemini-3.8-flash`); nova tentativa automática para erros temporários do Gemini (5xx e tempo esgotado) após falhas de resumo por HTTP 503; resumo passou a ter visão geral + resumo por partes (antes limitado a ~250 palavras); modo JSON na revisão ativa após 2/5 rodadas falharem por JSON malformado; reescrita do RELATORIO.md na estrutura do enunciado, a partir das evidências do projeto; função Conferir anotações criada e depois removida a pedido do usuário, por ser considerada próxima do NotebookLM | `frontend.py`, `ui.py`, `tutor_ui.py`, `providers.py`, `summary.py`, `tutor.py`, `assets/styles.css`, testes e documentação, incluindo `docs/RELATORIO.md` | Pendente de revisão humana | Commits no repositório; 89 testes automatizados aprovados; chamadas reais curtas ao Gemini apenas para diagnóstico ("Responda apenas: ok"), sem conteúdo do material, e um resumo de teste com texto repetido da demonstração (11 chamadas, concluído; no formato novo, ~2.060 palavras em 10 partes) |
| 17–18/11/2026 | Claude Code (Claude Opus 5.5) | Troca do projeto para o AlertaGolpe, a pedido do grupo, após comparação do EstudaPDF com o NotebookLM; catálogo de 16 golpes a partir de fontes públicas; regras locais; análise com Gemini (modo JSON e validação de trechos); interface com tema de alerta; conjunto de avaliação fictício (20 golpes, 12 legítimas) e script `avaliar.py`; reescrita do RELATORIO.md e geração do Word/PDF; modelos reserva automáticos (18/11) | `src/alertagolpe/`, `tests/test_alertagolpe.py`, `avaliacao/`, `avaliar.py`, `assets/styles.css`, `README.md`, `docs/RELATORIO.md` | Pendente de revisão humana | 54 testes automatizados; avaliação real com `gemini-3.5-flash-lite` em 17/11: regras 21/32, regras + catálogo + IA 32/32 (após nova tentativa para 2 respostas com JSON inválido); resultado em `output/avaliacao-resultados.json` |
| A preencher | A preencher | A preencher | A preencher | A preencher | A preencher |

Separar ao menos estas finalidades:

- Assistência na escrita e correção de código.
- Assistência na redação, revisão e organização dos materiais.
- Exploração de prompts no Ollama local; Google AI Studio somente se utilizado.
- Geração integrada ao aplicativo via Ollama ou Gemini, com o resultado real registrado.
- Eventual uso de outras ferramentas na gravação e edição.

Para chamadas do aplicativo, registrar provedor, identificador do modelo,
parâmetros relevantes, data e finalidade. Não armazenar credenciais nem
conteúdo pessoal. O texto de uma resposta simulada não comprova uma chamada real.

## Participação do grupo

O projeto pertence a um grupo de seis integrantes. A execução foi inicialmente
informada como concentrada em um integrante. Preencher atividades efetivas,
sem atribuir contribuição por suposição.

| Integrante | Atividades efetivamente realizadas | Materiais conferidos/produzidos |
| --- | --- | --- |
| Nome 1 | A preencher | A preencher |
| Nome 2 | A preencher | A preencher |
| Nome 3 | A preencher | A preencher |
| Nome 4 | A preencher | A preencher |
| Nome 5 | A preencher | A preencher |
| Nome 6 | A preencher | A preencher |

## Texto de declaração a adaptar

> Utilizamos assistência de IA nas atividades descritas neste registro. Os
> arquivos e as respostas foram revisados nas etapas identificadas, e as decisões
> humanas e limitações observadas estão documentadas. No aplicativo, o modelo
> generativo recebeu a pergunta e os trechos recuperados do documento. Os
> integrantes realizaram as atividades de gravação, edição e apresentação
> indicadas no registro de contribuições.

Usar essa declaração somente depois de preencher e verificar as atividades.
Enquanto a revisão, a integração ou a produção audiovisual estiverem pendentes,
declarar a pendência em vez de manter o texto no passado.

Se o resumo for efetivamente executado, acrescentar à declaração os modelos,
intervalos e etapas utilizados, explicando que o provedor recebeu o texto
extraído selecionado. Não acrescentar essa atividade no passado antes da execução.

## Cuidados para a entrega

- O nome e a versão do modelo devem corresponder ao que foi executado.
- Mostrar fontes e trechos não garante que uma resposta esteja correta.
- Busca sem geração e demo interna devem permanecer identificadas.
- Resultados, custos e tempos somente quando observados ou medidos.
- Chaves e documentos privados ficam fora do pacote e das gravações.
- Gravação e edição precisam ser realizadas pelos integrantes, conforme o enunciado.

## Referências

- Ollama e API local: https://docs.ollama.com/api
- Terminal do Ollama: https://docs.ollama.com/cli
- Gemini opcional: https://ai.google.dev/gemini-api/docs
- Documentação de referência de cada biblioteca: consultar os links em RELATORIO.md.
