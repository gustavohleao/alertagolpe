# Tutor de revisão — escopo implementado

## Problema e proposta

Ler um PDF não informa ao estudante quais conceitos consegue explicar por conta
própria. O EstudaPDF organiza prática com perguntas abertas, feedback fundamentado
e prioridades de revisão. A proposta é uma hipótese de utilidade: a eficácia
educacional ainda precisa ser avaliada; não há evidência de ganho de aprendizagem.

## Fluxo funcional

1. Carregar PDF textual ou usar o material de demonstração.
2. Informar um assunto com termos presentes no texto e autorizar o envio.
3. TF-IDF e cosseno recuperam até três trechos; sem evidências não há chamada.
4. Gemini prepara três perguntas, respostas esperadas e dois critérios por pergunta.
5. O estudante responde antes de a interface revelar o gabarito.
6. Gemini avalia cada critério contra a resposta e as evidências da pergunta.
7. O código soma os critérios atendidos (0–2), sem aceitar uma nota livre do modelo.
8. O painel agrega por assunto e ordena primeiro as menores proporções de critérios
   atendidos. Nova rodada no mesmo assunto inclui até 12 perguntas respondidas
   anteriormente no prompt, solicitando outras abordagens, sem garantir novidade.

Uma rodada usa uma chamada para geração e até três para correção. Não há
repetição automática. Falha da API não produz uma resposta simulada.
O histórico e as evidências ficam na sessão e podem ser exportados em JSON.
Trocar o documento ou limpar a sessão remove o acompanhamento anterior.

## Limites e transparência

As perguntas cobrem os trechos recuperados, não todo o documento. A recuperação
lexical pode perder sinônimos. Fontes desconhecidas e estruturas inválidas são
rejeitadas; uma fonte válida não comprova a correção semântica do resultado.
Perguntas/gabaritos e correções podem estar errados. Quando o modelo informa
que não consegue sustentar a correção, ela fica fora do indicador. A indicação
também pode falhar. O painel é formativo, não uma nota oficial nem diagnóstico.
Rodadas podem ter dificuldades diferentes; percentuais não demonstram evolução
de aprendizagem. O histórico não persiste entre sessões e não há contas.

Gemini recebe o assunto, até três trechos e as respostas, mediante autorização
específica. O download pode conter dados pessoais e texto do material.
Código, interface, testes e este documento foram produzidos com assistência de
IA e precisam de revisão do grupo. Os prompts executáveis estão em
`src/estudapdf/tutor.py` (tutor-v1).

## Avaliação prática a realizar antes da entrega

Escolher um material autorizado e três assuntos. Para cada rodada, uma pessoa
deve verificar se as perguntas são respondíveis e se o gabarito e critérios
estão sustentados. Testar respostas corretas, incompletas, incorretas e uma
tentativa de instruir o avaliador a dar pontuação máxima. Registrar divergências
entre a avaliação humana e a IA, além de tempo, falhas e chamadas utilizadas.
Testar assunto ausente e confirmar que não é gerada uma rodada sem evidências.

Os testes automatizados usam respostas simuladas do provedor para verificar
contratos, consentimento, referências e cálculo dos indicadores. Não comprovam
qualidade pedagógica nem disponibilidade real da API. A validação real do novo
fluxo e a avaliação com estudantes continuam pendentes.

## Encaixe no trabalho

Aplicação: tutor com prática e acompanhamento por sessão. Técnica de IA:
recuperação lexical por TF-IDF/cosseno integrada à geração (RAG). Exploração:
registrar ferramentas realmente usadas e comparações efetivamente realizadas.
Visão crítica: analisar perguntas inadequadas, correções divergentes e efeitos
das limitações da recuperação. Vídeo tutorial de aproximadamente dez minutos
continua sendo uma entrega separada, gravada e editada pelo grupo.

Este documento atualiza o foco do produto; relatório, slides e roteiro anteriores
devem ser revisados pelo grupo com os resultados reais, sem reaproveitar pilotos
históricos como se fossem validação deste fluxo.
