# Registro técnico de validação — 16/11/2026

Este registro descreve execuções feitas com assistência de Codex. Não equivale
a revisão humana, validação de aprendizagem ou avaliação independente.

> **Atualização em 17/11/2026:** a interface deixou de exibir as caixas de
> autorização de envio ao Gemini (pergunta, revisão e resumo). O envio passa a
> ocorrer quando o usuário aciona a ação. As menções a autorização abaixo
> descrevem o estado anterior.

## Ambiente

Python 3.12.10 portátil em `.tools/python/python.exe`. Streamlit 1.67.0,
pypdf 7.1.0 e scikit-learn 1.9.1. As demais versões estão registradas em
`requirements-lock.txt`. `pip check` não apontou incompatibilidades.

O ambiente anterior foi removido junto com o detector de golpes por solicitação
do usuário. O código novo está diretamente na raiz da pasta de trabalho.

## Testes automatizados

**35 testes aprovados:** nove de documentos, oito de recuperação, sete de
provedores, sete de orquestração e quatro da interface via Streamlit AppTest.
Os testes de protocolos HTTP usam respostas simuladas e não fazem geração real.

Cobertura relevante: extração de PDF textual criado em memória; página vazia
sem renumerar a seguinte; PDF protegido ou inválido; OCR não suportado;
divisão com sobreposição; relevância e preservação da localização; falhas de
conexão e respostas truncadas; IDs desconhecidos; ausência de evidência sem
chamar o modelo; exportação sem chave; resposta exibida como texto, sem imagens
remotas interpretadas pelo navegador.

O servidor em `http://127.0.0.1:8501` respondeu HTTP 200 em sua rota de saúde.
Uma tentativa de abrir o navegador automatizado falhou na inicialização da
ferramenta; não foi feita inspeção visual no navegador. Os testes de interface
foram executados pelo AppTest e passaram.

## Recuperação no exemplo interno

Executado `avaliar.py` sem `--gerar`. Dez perguntas no texto educativo interno,
não em um PDF real. Nas oito perguntas com seção de referência, a seção esperada
apareceu entre até três resultados em **8/8** casos. As duas perguntas com
informação ausente não recebem nota automática. Há trechos recuperados mesmo
em perguntas sem resposta: isso mostra que coincidência lexical não prova
relevância nem suficiência.

Registro: `output/avaliacao-demo.json`. O exemplo e as perguntas foram preparados
com assistência de IA e não constituem benchmark independente. Esta medida não
é acurácia de respostas e não comprova generalização para outras apostilas.

## Geração real local

O serviço Ollama respondeu à listagem e informou `llama3.2:1b` e `qwen2.5:3b`.
Uma consulta real com `qwen2.5:3b` foi concluída em **133,11 segundos**:

- Pergunta: “Como funciona a geração aumentada por recuperação RAG?”
- Fonte recuperada: seção 2 do material interno, identificador `[P2-T1]`.
- Resposta: definiu RAG, descreveu divisão, recuperação e uso do contexto,
  explicou que o fluxo não altera os pesos do modelo e apresentou limitações.
- Referência citada existente e conteúdo coerente na conferência assistida por IA.

Registro: `output/validacao-ollama.json`. Uma pergunta não demonstra qualidade
geral. A latência é alta; o timeout local foi configurado para 180 segundos.
Gemini está implementado e testado com HTTP simulado, mas não foi chamado
com uma conta real por ausência de chave configurada.

Uma segunda tentativa com `llama3.2:1b`, na mesma pergunta, levou **25,081
segundos**, mas respondeu “Não encontrei informação suficiente no material.”
Apesar de concluir a chamada, a resposta foi uma recusa indevida nesta
conferência assistida por IA, pois a seção 2 continha a explicação. O arquivo
`output/validacao-ollama-1b.json` preserva o registro. O `.env` manteve Qwen.
Esse piloto não é uma comparação controlada: houve diferença de modelo,
condições de carregamento/cache e uma alteração na instrução de formatação
do prompt. Não atribuir diferenças exclusivamente ao tamanho dos modelos.

## Pendências da entrega

Revisar o código e o material educativo; escolher uma apostila autorizada;
executar a avaliação de recuperação e respostas com esse PDF; registrar erros
e revisores; conferir a interface visualmente; completar o relatório; montar
os slides finais; gravar e editar o tutorial; ensaiar a apresentação. Os
materiais em Markdown são rascunhos e roteiro, não uma gravação ou um PPTX.

## Atualização do frontend — 17/11/2026

Interface redesenhada com assistência de Codex: identidade visual verde e tons
claros, barra lateral de material/consulta, workspace, formulário e painel de
evidências. As configurações de provedor ficam em uma área recolhida.

Os 35 testes passaram novamente após a refatoração. Foi feita inspeção visual
das capturas reais no Edge headless, em 1440 × 1100 e 390 × 844, além de uma
verificação mobile com emulação de dispositivo. Não houve overflow horizontal
nem exceções Streamlit. A busca no navegador encontrou uma evidência na demo,
mantendo o modo sem geração e sem consultar provedores.

Foram corrigidos ícones ausentes, sidebar expandida no celular e contraste
do texto de upload. Os trechos longos usam uma região de rolagem. A resposta
do modelo e os trechos continuam em texto simples; nomes e perguntas usados
em componentes HTML são escapados. Os ícones são locais, sem carregamento
de imagens ou fontes de terceiros.

Capturas: `output/ui-desktop.png`, `output/ui-mobile.png` e `output/ui-result.png`.
Essa conferência de interface não substitui a avaliação com uma apostila real
nem a revisão humana dos resultados e da apresentação.

## Resumo do material — 17/11/2026

Adicionado um fluxo próprio, separado da busca RAG top 3: selecionar o intervalo,
planejar todos os segmentos do texto extraído, resumi-los e combinar as notas.
Há limites de 60 mil caracteres, orçamento de 6 mil bytes UTF-8 por prompt e
plano de até 20 chamadas. A interface informa o volume antes da geração;
Gemini exige autorização própria para todo o texto selecionado.

**61 testes aprovados:** os 35 anteriores, 21 de resumo e cinco da interface
do resumo. Há cobertura da última página, páginas repetidas, contexto UTF-8,
mapas/sínteses em vários níveis, referências por ramificação, ausência de
autorização com zero chamadas, erros sem parcial completo e exportação sem chave.
As respostas dos testes automatizados são simuladas, não avaliações de qualidade.

No Edge headless, desktop e mobile não apresentaram overflow ou exceções.
A prévia mostrou quatro seções, 3.312 caracteres e até uma chamada. O intervalo
1–2 atualizou para duas seções e 1.612 caracteres. O botão ficou desabilitado
em Somente busca. Esse QA não executou geração. Capturas em `ui-summary.png`
e `ui-summary-mobile.png`, na pasta `output`.

### Pilotos reais de resumo

As duas primeiras tentativas com `qwen2.5:3b` concluíram a chamada, mas foram
rejeitadas por não apresentarem IDs. O texto bruto não foi preservado, então
não é possível avaliar sua qualidade. Registros de erro:
`output/validacao-resumo-ollama.json` e `output/validacao-resumo-ollama-v2.json`.

A política final mantém a rejeição de IDs desconhecidos e de notas intermediárias
sem referências, mas permite um texto final sem IDs com aviso explícito. O painel
mostra **Texto processado**, sem apresentar entradas como citações do modelo.
O aviso acompanha os downloads. Isso não torna as afirmações automaticamente
corretas nem resolve a limitação de um modelo que falha em citar nas etapas intermediárias.

O terceiro piloto local foi concluído em **99,018 segundos**, com uma chamada,
as quatro seções da demo e 3.312 caracteres processados. O texto final não trouxe
IDs e gerou o aviso esperado. O registro completo está em
`output/validacao-resumo-ollama-v3.json`.

Na conferência assistida por IA, o texto mencionou os quatro temas do material,
mas a frase inicial associou de forma ambígua classificação e regressão ao
aprendizado supervisionado e não supervisionado. Isso pode induzir uma atribuição
conceitual incorreta. Não considerar o resumo aprovado por humanos. O piloto
não usou PDF real nem validou qualidade geral ou múltiplas etapas com um modelo
real; a hierarquia foi testada com respostas simuladas. Gemini continua sem
chamada real registrada neste projeto.

## Diagnóstico de conexão Gemini — 17/11/2026

O usuário relatou falha ao consultar modelos: “Não foi possível conectar ao
provedor”. Um GET ao endpoint oficial `/v1beta/models`, sem chave ou documentos,
no mesmo contexto isolado em que o app havia sido iniciado, resultou em
`ConnectError → ConnectError → PermissionError`, WinError 10013.

O mesmo diagnóstico em processo com acesso externo permitido recebeu HTTP 403,
esperado para esse pedido sem credenciais. Isso confirma alcance da API, não
validade da chave ou permissão de uma conta. O servidor foi reiniciado fora
desse bloqueio de rede. Não foram alteradas configurações de firewall ou TLS.

Também foi corrigida a normalização da chave em consultas de modelos e geração:
espaços externos são removidos e espaços/quebras internos produzem erro específico,
sem exibir a chave. Os testes usam somente credenciais fictícias e HTTP simulado.

Após essa correção, a suíte completa teve **65 testes aprovados**. O próprio
método `list_models`, executado com acesso externo permitido e uma chave
fictícia com espaços externos, alcançou o Google e recebeu a rejeição de
autenticação/parâmetros esperada. Não houve uso de chave real, documentos ou
geração nesse diagnóstico. A tentativa adicional via navegador headless não
concluiu a interação com o seletor antes do botão; não é evidência de validação
de uma conta. O servidor final foi reiniciado com acesso à rede permitido.

A validade, as permissões e a cota da chave verdadeira continuam dependendo
da configuração do usuário e da resposta da API. No fluxo anterior usado
durante esse diagnóstico, chaves digitadas somente na interface podiam precisar
ser informadas novamente após reiniciar o servidor. Esse comportamento é
histórico e foi substituído pelo fluxo abaixo.

## Configuração privada da chave — atualização de 17/11/2026

A entrada de chave/senha foi removida da interface a pedido do usuário. A
configuração passa a carregar `GEMINI_API_KEY` automaticamente do `.env` privado
do projeto ou do ambiente do servidor. Para Gemini, definir `LLM_PROVIDER=gemini`;
`LLM_MODEL` pode ficar sem valor até consultar e selecionar um modelo disponível.
Provedor e seleção de modelo permanecem na interface, que mostra somente se
a chave está definida ou ausente.

O arquivo é relido a cada reexecução; depois de editá-lo, atualizar a página
sem reiniciar o servidor. Variáveis explicitamente definidas no ambiente do
processo têm prioridade sobre o `.env`. Não embutir a chave em fonte
compartilhável nem enviá-la pelo chat. Os consentimentos de pergunta e resumo
permanecem separados e obrigatórios antes dos respectivos envios.

Os resultados históricos de 35, 61 e 65 testes não foram alterados. A contagem
posterior à mudança é de **76 testes aprovados**: os 65 anteriores, oito de
configuração e três de integração com a interface. Eles verificam a releitura
do arquivo, prioridade do ambiente, ausência de mutação do processo, ausência
de campo/exibição da chave e invalidação dos modelos em cache após uma mudança.
Foram usadas credenciais fictícias e consultas simuladas; isso não comprova
autenticação de conta real.
