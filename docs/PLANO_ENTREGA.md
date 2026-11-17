# Plano de entrega — EstudaPDF

**Data de elaboração:** 16/11/2026  
**Atualização de escopo:** 17/11/2026 — resumo global implementado, com avaliação inicial.  
**Entrega:** 19/11/2026 — confirmar horário e canal da disciplina.  
**Contexto:** grupo de seis; execução atualmente concentrada em um integrante.

Este plano considera a capacidade de execução de uma pessoa. A entrega continua
sendo do grupo. Outras contribuições devem ser registradas conforme ocorrerem,
sem presumir que alguma atividade já foi feita por um integrante.

## Escopo obrigatório do protótipo

- Interface local em Streamlit com “Sala de estudo”, “Resumir material” e
  “Como funciona”.
- Um PDF textual por vez, até 15 MB e 150 páginas.
- Extração por página; trechos de cerca de 1.100 caracteres, sobreposição de 180.
- Recuperação lexical com TF-IDF de unigramas/bigramas e normalização de acentos.
- Até três trechos com cosseno a partir de 0,05; parâmetro operacional não calibrado.
- Pergunta e contexto enviados ao Ollama local configurado; Gemini como alternativa.
- Resposta e evidências visíveis para conferência.
- Modo somente busca explícito, sem apresentar resposta fixa como geração.
- Demo interna identificada como texto em seções, sem fingir leitura de PDF.
- Tratamento de falhas e instruções para execução.

## Novo fluxo de resumo — atualização de 17/11

O recurso implementado usa todo o texto extraído das páginas selecionadas,
por mapa e síntese, e exige o modo de resposta com IA. Ele é distinto de
perguntas RAG, que recuperam até três trechos relacionados à pergunta.

Critérios implementados, a conferir na demonstração:

- Verificar antes de gerar: até 60 mil caracteres, até 20 chamadas previstas
  e orçamento de 6 mil bytes UTF-8 por prompt, usado como heurística conservadora.
- Solicitar intervalo menor quando necessário, sem truncamento silencioso.
- Exigir fontes originais `[P12-R1]` nas notas intermediárias, distintas das
  referências RAG `[P12-T1]`. Referências emitidas pela síntese devem ser conhecidas.
- Permitir saída final sem IDs somente com aviso e origens rotuladas como
  “Texto processado”, não “Fontes citadas”, sem inventar citações. Incluir o
  aviso no TXT e no campo `warning` do JSON.
- Manter rejeição de notas intermediárias sem referências, IDs desconhecidos,
  texto vazio, recusa sem resumo, saída longa e outras falhas de etapa.
- ~~Exigir consentimento Gemini específico para todo o texto extraído do intervalo,
  separado da autorização para perguntas.~~ Removido em 17/11/2026 por decisão do
  grupo: a interface não exibe mais caixas de autorização.
- Não apresentar resultado parcial como completo quando uma etapa falhar.
- Exportar TXT/JSON sem chave quando o usuário decidir; manter o estado em
  memória da sessão, sem afirmar que a exportação o apaga.
- Informar que resumo pode omitir pontos e que imagens/tabelas mal extraídas
  não foram compreendidas.

Dois pilotos reais de resumo qwen2.5:3b concluíram HTTP, mas tiveram saída
rejeitada por ausência de IDs. Registros: `output/validacao-resumo-ollama.json`
e `output/validacao-resumo-ollama-v2.json`. Os textos brutos não foram preservados;
qualidade desconhecida. Após o ajuste final, **61 testes passaram**: 35 anteriores,
21 do resumo e cinco da interface. O terceiro piloto `qwen2.5:3b` concluiu em
99,018 s, processando quatro seções/3.312 caracteres em um mapa e uma chamada,
com aviso de falta de IDs. Registro: `output/validacao-resumo-ollama-v3.json`.

A resposta abordou os quatro temas, mas a primeira frase pode confundir tarefas
supervisionadas e não supervisionadas. Essa limitação foi observada com
assistência de IA, sem aprovação humana ou qualidade geral validada. A
conferência headless desktop/móvel verificou o plano de quatro seções e o
intervalo 1–2 atualizado para duas seções/1.612 caracteres, sem chamadas ao modelo.
Os resultados de 16/11 abaixo pertencem às perguntas. Nenhum novo Gemini real testado.

Confirmar os parâmetros na implementação final. Não ampliar o escopo para OCR,
WhatsApp, múltiplos usuários, banco vetorial ou publicação externa nesta entrega.

## Cronograma

| Data | Trabalho prioritário | Critério verificável |
| --- | --- | --- |
| 16/11 | Preparar ambiente, extrair documento, recuperar trechos, testar provedor | Aplicativo abre e uma chamada real ao modelo foi conferida; busca sem chave funciona como busca |
| 17/11 | Concluir o novo resumo, tratar falhas, avaliar os dois fluxos e atualizar relatório | Perguntas e resumo distinguidos; limites e consentimento conferidos; PDF real e resultados registrados quando executados |
| 18/11 | Congelar funcionalidades, finalizar relatório/slides, gravar/editar tutorial, ensaiar | Arquivos revisados, vídeo reproduzido integralmente e demonstração ensaiada |
| 19/11 | Conferir pacote e enviar | Código, instruções e materiais acessíveis antes do prazo |

Se o cronograma atrasar, cortar acabamento e extensões. O modo somente busca
ajuda a diagnosticar o fluxo, mas não atende sozinho ao requisito de IA generativa.
Uma opção de provedor na interface não comprova integração funcionando.

## Participação e conferência humana

O responsável pela execução deve revisar o código e compreender o fluxo.
Se outros integrantes participarem, podem assumir revisão do documento,
conferência de fontes, gravação, edição, revisão textual e ensaio. Atualizar
o registro de contribuições com atividades reais.

Codex pode auxiliar código, correções, documentação, diagrama e roteiro. O
grupo precisa conferir os resultados, adaptar o texto e produzir a gravação
e edição exigidas pelo enunciado.

## Avaliação mínima

### Estado inicial já observado em 16/11

- 35 testes automatizados passaram: 17 núcleo, sete provedores, sete serviço e
  quatro interface. As requisições HTTP dos testes são simuladas. O teste extra
  verifica exibição da resposta como texto simples, evitando imagens remotas.
- Endpoint de saúde do aplicativo respondeu HTTP 200.
- Demo interna textual: seção esperada no top 3 em 8/8 perguntas positivas;
  dez casos ao todo, duas sem resposta fora dessa contagem e sem nota de geração.
- A demo tem autoria assistida por IA, não é PDF e não é avaliação independente.
- Ollama em `127.0.0.1:11434` lista `llama3.2:1b` e `qwen2.5:3b`.
  Uma geração real com `qwen2.5:3b` foi concluída em 133,11 s, com timeout local
  configurado em 180 s. Registro: `output/validacao-ollama.json`.
- A resposta sobre RAG usou `[P2-T1]` e conteúdo coerente com a seção 2, segundo
  revisão assistida por IA, não humana. Uma pergunta da demo não valida qualidade
  geral ou PDF real.
- A segunda execução, com `llama3.2:1b`, terminou em 25,081 s, mas recusou
  indevidamente a mesma pergunta apesar do contexto suficiente. Registro:
  `output/validacao-ollama-1b.json`. Revisão assistida por IA. Piloto não controlado,
  com diferenças de ordem/cache e pequenas diferenças de formatação do prompt;
  não atribuir o resultado somente ao tamanho do modelo. Manter qwen2.5:3b.
- Gemini não foi testado sem chave. Avaliação de PDF real e revisão humana faltam.

### Próximas verificações

Preparar dez perguntas com referências antes de consultar o aplicativo:
seis respondíveis, uma paráfrase, duas sem suporte e uma tentativa de alterar
as instruções. Anotar recuperação, resposta, referências e problemas reais.
Registrar quais casos foram usados para ajustes e separar casos adicionais
para a conferência final.

Também exercitar entrada vazia, arquivo inválido, PDF sem texto, limite de
tamanho/páginas, ausência de chave e indisponibilidade do provedor. Distinguir
testes simulados de chamadas externas reais. Não preencher métricas sem execução.

Para o resumo, revisar manualmente cobertura e fidelidade de um intervalo curto,
preservação das referências originais e ausência de cortes ocultos. Testar
limites, falhas intermediárias e exportações sem chave.
O resultado 8/8 da recuperação não é uma nota de cobertura do resumo. Os
61 testes e o terceiro piloto concluído não substituem revisão humana, PDF
real ou avaliação de síntese em múltiplas chamadas. O caso real curto fez
somente uma chamada.

## Pacote de entrega

- [ ] Código-fonte com dependências e instruções de instalação/execução.
- [ ] Configuração de exemplo sem chave e sem segredos.
- [ ] Documento demonstrável público, próprio ou autorizado.
- [ ] Prompts efetivos e diagrama conferido com o código.
- [ ] Relatório concluído com resultados reais e limitações.
- [ ] Conteúdo dos slides revisado e adaptado ao formato solicitado.
- [ ] Tutorial próprio de aproximadamente dez minutos, com demonstração da ferramenta.
- [ ] Registro de ferramentas de IA e contribuições do grupo.
- [ ] Resumo: revisão humana de cobertura, referências e limites,
  com distinção entre estado concluído e falha parcial.
- [ ] Demonstração ensaiada e cópia de segurança identificada como gravação.
- [ ] Pacote sem ambiente virtual, chaves ou documentos privados.

## Estado documental

Os Markdown preparados são rascunhos. No fluxo de perguntas, há duas execuções reais: uma
resposta coerente com latência alta e uma recusa indevida mais rápida. Ainda
faltam revisão humana, avaliação com PDF real e
produção do vídeo. Os resultados iniciais não representam validação geral.
Atualizar o estado com evidências durante o desenvolvimento. O tutorial
principal ensina Ollama local.
O resumo implementado em 17/11 teve dois pilotos rejeitados e um concluído
com aviso e ambiguidade conceitual observada. Há 61 testes e conferência
headless da interface, sem aprovação humana ou validação em PDF real. O grupo tem seis
integrantes e a execução permanece concentrada no usuário, conforme informado.
