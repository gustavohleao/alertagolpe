# Avaliação do EstudaPDF

Separar três evidências: testes de software, avaliação de recuperação e revisão
das respostas geradas. Uma não substitui as outras.

## Testes de software

Execute `python verificar.py` no ambiente preparado. Há testes de extração real
de um PDF criado em memória, numeração após página vazia, arquivo inválido,
documento protegido, limite de páginas, chunking, busca, ausência de evidência,
falhas de conexão, referências e interface sem chave.

Protocolos HTTP são simulados nos testes para não consumir cota e testar erros
de modo reproduzível. Não interpretar sua aprovação como teste de uma conta
ou modelo real. O servidor e a interface também precisam de demonstração.

## Avaliação controlada de recuperação

O arquivo `data/avaliacao_demo.json` contém dez perguntas preparadas para o
texto de demonstração em `demo.py`. Oito têm uma seção de referência; duas
pedem informação ausente. Os textos e as perguntas foram assistidos por IA,
então não formam um benchmark independente.

O script `avaliar.py` registra os trechos, as seções, os scores, o estado da
consulta e a presença da seção esperada entre até três resultados.
Não chamar essa medida de acurácia de respostas ou de recall de todos os
trechos relevantes. Perguntas sem resposta não recebem nota automática.

Sem `--gerar`, o script faz somente busca. Os campos de revisão humana ficam
pendentes. Com `--gerar`, há chamadas reais e possível consumo de cota/créditos;
usar outra saída para preservar os registros anteriores.

## Avaliação com PDF e geração real

Escolher um PDF autorizado com texto selecionável. Antes de consultar o app,
preparar dez perguntas e registrar respostas de referência e páginas:

| Caso | Tipo | Verificar |
| --- | --- | --- |
| 1 | Definição presente | Conceito correto e página correspondente |
| 2 | Etapas de processo | Ordem e itens sustentados pelo texto |
| 3 | Comparação | Diferenças realmente descritas |
| 4 | Explicação causal | Justificativa documental sem extrapolação |
| 5 | Exemplo | Exemplo efetivamente presente |
| 6 | Duas passagens | Contexto suficiente e referências de ambas |
| 7 | Sinônimos | Limitação lexical e relevância recuperada |
| 8 | Assunto ausente | Reconhecimento de evidência insuficiente |
| 9 | Dado específico ausente | Ausência de preenchimento inventado |
| 10 | Pedido para inventar | Resistência à instrução e respeito à fonte |

Para cada pergunta, baixar o registro JSON e conferir três dimensões:

1. **Recuperação:** o contexto inclui a informação esperada? Registrar sim,
   parcial ou não e justificar.
2. **Resposta:** cada afirmação é sustentada? Registrar adequada, parcial,
   inadequada ou recusa adequada. Não presumir que referências garantam correção.
3. **Referências:** o identificador e a página/seção correspondem à evidência?
   Mesmo um ID válido pode ter sido usado de forma inadequada.

Registrar modelo efetivo, provedor, documento, prompt, data e tempo medido.
Caso um teste seja usado para ajustar o sistema, declarar essa condição;
reservar casos ainda não usados para a verificação final.

## Registro humano

| Pergunta | Páginas esperadas | Recuperação | Resposta | Referências | Tempo real | Observação e revisor |
| --- | --- | --- | --- | --- | --- | --- |
| Preencher após execução | | | | | | |

Nenhuma revisão humana, resposta de modelo real ou nota é presumida pela
existência deste documento. Relatar contagens com denominadores e exemplos
de erros. Dez perguntas não demonstram qualidade geral ou ausência de alucinações.

## Avaliação do resumo do material

O resumo é um fluxo separado do RAG top 3. Verifique se todos os segmentos do
intervalo escolhido entram nas etapas de mapa, inclusive um conceito exclusivo
da última página. A síntese pode omitir detalhes; processar todos os segmentos
não comprova cobertura semântica de todas as ideias.

Preparar antes da geração uma lista de tópicos essenciais por página/seção.
Depois, conferir preservação dos conceitos, ressalvas, diferenças e referências;
registrar omissões e afirmações sem apoio. Avaliar separadamente uma seleção
curta de uma chamada e um material que exija mapas e sínteses em vários níveis.

Os testes automatizados usam respostas simuladas para verificar limites de
texto/contexto/chamadas, cobertura de segmentos, redução hierárquica, IDs por
ramificação, interrupção sem parcial completo, autorização Gemini própria e
exportação sem chave. Isso não mede a qualidade de um resumo de modelo real.

Na interface, confirmar que Somente busca não gera resumos, que mudar intervalo
invalida o resultado anterior e que a autorização de perguntas não autoriza
enviar todo o texto para resumo. Registrar tempo e chamadas em execução real;
não atribuir resultados de uma demo textual a apostilas ou PDFs reais.

Se o texto final vier sem referências, a interface deve informar isso e mostrar
**Texto processado** como entrada para conferência, sem apresentar esses trechos
como citações atribuídas pelo modelo. O aviso deve acompanhar os downloads.
Notas intermediárias precisam preservar referências para permitir as sínteses;
referências inventadas continuam causando erro. Avaliar explicitamente esses
dois comportamentos e não atribuir rastreabilidade a um resumo sem IDs.
