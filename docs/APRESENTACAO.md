# EstudaPDF — conteúdo de oito slides

Rascunho para apresentação oral. Converter para o formato exigido pela disciplina
após conferir a implementação. Não incluir resultados ainda não medidos.

## Slide 1 — O problema e a proposta

**EstudaPDF: perguntas e respostas apoiadas em documentos**

- Problema: localizar e compreender informações em apostilas extensas.
- Proposta: recuperar trechos e usá-los como contexto para uma explicação gerada.
- Público inicial: estudantes.
- Grupo: preencher nomes e contribuições reais.

**Fala sugerida:** apresentar um exemplo concreto de dúvida sobre uma apostila.
Explicar que o usuário precisa conferir a resposta nas fontes.

## Slide 2 — O que o aplicativo faz

- Recebe um PDF textual e uma pergunta.
- Recupera trechos relacionados à pergunta.
- Quando há provedor configurado, gera uma resposta usando o contexto recuperado.
- Exibe trechos e referências para conferência.
- Oferece modo somente busca, explicitamente sem geração.
- Recurso “Resumir material”, sobre todo o texto extraído
  de um intervalo escolhido. Exige resposta com IA e não usa somente o top 3.

**Limites implementados:** um PDF por vez, até 15 MB e 150 páginas; sem OCR.
Teste de um PDF real e revisão humana ainda pendentes.

## Slide 3 — RAG e arquitetura

```text
PDF → extração por página → trechos → TF-IDF
                                      ↓
Pergunta → representação TF-IDF → similaridade do cosseno
                                      ↓
                         até três trechos relevantes
                                      ↓
                           prompt + Ollama/Gemini
                                      ↓
                          resposta + fontes visíveis
```

- RAG: recuperação de evidências antes da geração.
- Recuperação lexical; não é busca com embeddings semânticos.
- A busca pode falhar quando pergunta e documento usam vocabulários diferentes.

**Outro fluxo — resumo global implementado:** intervalo selecionado →
blocos de todo o texto extraído → mapa → síntese com fontes originais.
Referências de resumo `[P12-R1]` são distintas das referências RAG `[P12-T1]`.
Notas intermediárias exigem referências originais. Uma saída final sem IDs
é mostrada com aviso e origens rotuladas como “Texto processado”, sem inventar citações.

## Slide 4 — Ferramentas e decisões

| Ferramenta | Função |
| --- | --- |
| Streamlit | Interface |
| pypdf | Extração textual |
| scikit-learn | TF-IDF e cosseno |
| Ollama local | Provedor principal; geração real com qwen2.5:3b |
| Gemini REST | Alternativa opcional, sem chamada real por ausência de chave |
| Codex | Assistência de desenvolvimento e documentação |

Parâmetros implementados: trechos de aproximadamente 1.100 caracteres, sobreposição
de 180, unigramas/bigramas, até três resultados e limiar de cosseno 0,05.
**O limiar não é confiança calibrada.** Timeout local configurado em 180 s.

Resumo: até 60 mil caracteres e 20 chamadas previstas, verificados
antes de gerar; orçamento heurístico de 6 mil bytes UTF-8 por prompt. Excesso
exige intervalo menor, sem corte silencioso. Esse orçamento não equivale a tokens.

## Slide 5 — Demonstração

1. Identificar o PDF e sua autorização de uso.
2. Fazer uma pergunta com resposta localizada no documento.
3. Mostrar os trechos recuperados e conferir a página.
4. Exibir a resposta gerada pela chamada real.
5. Fazer uma pergunta sem suporte no documento e observar o comportamento.

Mostrar a aba “Resumir material” ao lado
de “Sala de estudo” e “Como funciona”: selecionar intervalo, conferir o plano,
gerar e exportar TXT/JSON sem chave. Em Gemini, mostrar o consentimento específico
para enviar todo o texto extraído do intervalo, diferente da autorização de pergunta.
Apresentar o aviso se faltarem IDs e conferir o texto: a conclusão técnica não
significa correção do resumo. A demonstração registrada usa a demo, não PDF real.

Usar a demo interna apenas com identificação explícita de texto em seções.
Não apresentar o modo somente busca como demonstração de geração.

## Slide 6 — Avaliação e resultados

**Resultados iniciais de desenvolvimento em 16/11/2026:**

- 35 testes passaram: 17 núcleo, sete provedores, sete serviço e quatro interface.
- HTTP dos testes simulado; geração real verificada separadamente.
- Servidor acessível: endpoint de saúde respondeu HTTP 200.
- Demo textual interna: seção esperada no top 3 em 8/8 perguntas positivas.
- Dez casos ao todo; duas perguntas sem resposta fora dessa contagem, sem nota de geração.
- Texto da demo com autoria assistida por IA; não é PDF nem avaliação independente.
- Uma geração real com `qwen2.5:3b` terminou em **133,11 s**, espera alta para uma interação.
- Resposta sobre RAG coerente com seção 2 e referência `[P2-T1]` existente,
  segundo revisão assistida por IA, sem revisão humana registrada.
- `llama3.2:1b` respondeu em 25,081 s, mas recusou indevidamente a mesma pergunta.
- Evidências: `output/validacao-ollama.json` e `output/validacao-ollama-1b.json`.
- Piloto não controlado: uma pergunta, ordem/cache e pequenas diferenças de formatação
  do prompt. Não atribuir a diferença somente ao tamanho dos modelos.

**Falta:** teste com PDF real, conferência humana e avaliação de mais respostas.
Gemini não foi testado sem chave. Esses resultados não comprovam qualidade geral das respostas.
Resumo em 17/11: dois pilotos `qwen2.5:3b` tiveram HTTP concluído, mas saída
rejeitada por ausência de IDs. Texto bruto não preservado: qualidade desconhecida.
Depois do ajuste, **61 testes passaram**: 35 anteriores, 21 do resumo e cinco da interface.
O terceiro piloto concluiu em **99,018 s**: quatro seções, 3.312 caracteres,
um mapa/uma chamada, sem IDs e com aviso. Evidência: `output/validacao-resumo-ollama-v3.json`.
Abordou os quatro temas, mas a primeira frase pode confundir as tarefas de
aprendizado supervisionado e não supervisionado. Revisão assistida por IA,
sem aprovação humana ou comprovação de qualidade geral.
QA headless desktop/móvel conferiu o plano e o intervalo 1–2, sem chamadas ao modelo.
Esses resultados são separados dos números de perguntas acima; o caso real
curto não valida síntese em múltiplas chamadas ou PDF real.

## Slide 7 — Visão crítica e ética

- Similaridade lexical pode deixar de recuperar informações relevantes.
- Extração pode perder tabelas, equações e estrutura.
- Modelo pode responder sem suporte ou citar fontes inadequadamente.
- Referências visíveis ajudam a conferir; não garantem correção.
- API externa recebe pergunta e contexto selecionado.
- Materiais autorizados, chaves protegidas e uso de IA declarado.
- Resumo pode omitir pontos; imagens e tabelas mal extraídas não são compreendidas.
- Falha de etapa não deve aparecer como resumo completo; notas intermediárias
  preservam fontes. Saída final sem IDs exige aviso, inclusive no TXT/JSON.
- “Texto processado” informa entrada utilizada, não comprova citação ou fundamento.
- IDs desconhecidos, texto vazio, recusa sem resumo e saída longa continuam rejeitados.
- Exportação pode conter dados do documento.

Separar limitações observadas nos testes de riscos ainda não exercitados.

## Slide 8 — Conclusões e próximos passos

**Conclusão provisória:** há evidências iniciais da execução do software, da
recuperação e de duas execuções reais de perguntas na demo. A resposta coerente teve latência
alta; a alternativa mais rápida recusou indevidamente. A avaliação
com PDF real e a revisão humana ainda precisam ser realizadas. Uma pergunta
não valida qualidade geral. No resumo, houve dois pilotos rejeitados e um
concluído com aviso e ambiguidade conceitual observada. Atualizar após a
revisão humana e antes da apresentação.

- Entrega: código, instruções, relatório, prompts, avaliação e tutorial.
- Melhorias possíveis: recuperação semântica/híbrida, OCR e avaliação maior.
- Assistência de IA: registrar ferramentas, tarefas e revisão humana.
- Em 17/11, Codex auxiliou na implementação, testes e documentação do resumo;
  revisão humana, PDF real e vídeo ainda pendentes.
- Referências: documentação oficial de Streamlit, pypdf, scikit-learn e Ollama;
  Gemini somente como alternativa.

**Fala final:** responder ao problema inicial com os resultados reais. Evitar
afirmar que o sistema eliminou erros ou que foi validado em larga escala.

## Apoio para o ensaio

Distribuir falas somente entre participantes efetivos. Todos os apresentadores
devem compreender a diferença entre recuperação e geração. Preparar uma gravação
de segurança identificada como gravação; ela não substitui o teste real da integração.
