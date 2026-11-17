# EstudaPDF

**Tutor de revisão baseado no material da disciplina.** O aluno escolhe um
assunto, responde a três perguntas abertas e recebe feedback com dois critérios
por resposta, gabarito e evidências. Um painel organiza prioridades de revisão
com base nas respostas desta sessão. Consulte [o fluxo e a avaliação](docs/TUTOR_REVISAO.md).

A interface oferece revisão ativa, perguntas e resumo do material. Provedor,
chave e modelo são gerenciados no servidor. `LLM_MODEL` fixa o modelo usado;
quando estiver vazio, o servidor seleciona automaticamente um modelo de texto
disponível, dando preferência à família Flash. As confirmações de envio de
conteúdo ao Gemini continuam disponíveis antes das operações.

A geração de respostas e resumos usa exclusivamente a API Gemini. Configure
`GEMINI_API_KEY` no `.env` privado e escolha um modelo disponível na conta.
Os pilotos Ollama
registrados nos materiais são históricos, anteriores à remoção desse suporte.

Assistente de estudos com **RAG (geração aumentada por recuperação)** sobre um
PDF escolhido pelo usuário. Encontra trechos relevantes e usa um modelo de
linguagem para responder com referências à fonte.

Projeto acadêmico de IA Generativa, entrega em **19/11/2026**, grupo de seis.
A execução está atualmente concentrada em um integrante. A participação
efetiva e a assistência de IA devem ser registradas nos materiais finais.

## Começar neste computador

Na pasta `D:\TrabalhoAI`, execute no PowerShell:

```powershell
& '.\.tools\python\python.exe' -m streamlit run app.py
```

Abra **http://127.0.0.1:8501**. O Python portátil e as dependências já foram
preparados localmente. Não é necessário ativar ambiente virtual ou instalar
Python novamente neste computador. A pasta `.tools` é ferramenta de ambiente,
não faz parte do código a entregar.

Também existe `iniciar.ps1`, se a política de scripts do computador permitir.
Não é necessário alterar a política de execução do Windows.

1. Comece com o material de demonstração ou carregue um PDF textual.
2. Em **Revisão ativa**, informe um assunto presente no material.
3. Leia e marque a autorização de envio ao Gemini, depois prepare a rodada.
4. Responda às perguntas, confira o feedback e as fontes e consulte o plano de revisão.
5. Use **Consultar material** para tirar dúvidas e baixe o histórico se desejar.

### Resumir seu material

Abra a aba **Resumir material**, escolha todo o intervalo disponível ou selecione
as páginas/seções desejadas. Autorize o envio do intervalo ao Gemini,
confira o volume e o limite de chamadas mostrados e clique em **Gerar resumo
do material**. O resultado pode ser baixado como texto ou registro JSON.

O resumo usa **todo o texto extraído do intervalo escolhido**, processado em
partes e combinado em uma síntese; não usa somente os três trechos do RAG de
perguntas. As fontes do resumo têm IDs como `[P12-R1]`; perguntas usam `[P12-T1]`.
O modelo continua podendo omitir detalhes ou interpretar algo incorretamente.
Imagens e páginas sem texto selecionável não são compreendidas.

Se o texto final não trouxer referências, ele é exibido com um aviso explícito.
O painel mostra **Texto processado**, sem inventar citações ou afirmar apoio
para cada conclusão. O aviso acompanha os downloads. Referências desconhecidas
e notas intermediárias sem fontes continuam impedindo a conclusão.

No Gemini, o resumo exige uma autorização própria para enviar **todo esse texto**.
A autorização de trechos de perguntas não se aplica ao resumo. Ela é vinculada
ao documento e intervalo escolhidos. No Ollama, o envio é ao serviço local.

Limites operacionais: até 60 mil caracteres e um plano com no máximo 20 chamadas
de IA, apresentado antes de começar. Cada prompt completo tem até 6 mil bytes
UTF-8 como orçamento conservador de contexto, não uma contagem exata de tokens.
Se exceder os limites, selecione menos páginas; o aplicativo não corta o fim
silenciosamente. Documentos longos podem consumir mais tempo/cota. Se qualquer
etapa falhar, um resumo parcial não é apresentado como concluído.

Validação de 17/11: **61 testes de software passaram**. Um resumo real das
quatro seções da demonstração foi gerado pelo Qwen local em **99,018 s**, sem
referências, com aviso explícito. Houve uma formulação conceitual ambígua na
conferência assistida por IA: revisar os resultados continua necessário.
Isso não comprova qualidade em apostilas reais nem revisão humana.

O exemplo interno é um texto educativo assistido por IA, dividido em seções.
Não é um PDF de uma disciplina nem um benchmark independente. Nos PDFs,
as referências preservam o número da página do arquivo, começando em 1,
que pode diferir da numeração impressa na apostila.

### Estado verificado em 16/11/2026

- 35 testes automatizados passaram, incluindo quatro da interface Streamlit.
- Servidor local respondeu HTTP 200.
- No exemplo interno, a seção esperada apareceu entre os três resultados nas
  oito perguntas com referência. Foram dez casos, incluindo dois sem resposta
  de referência que não entram nessa contagem. Isso avalia somente recuperação
  num exemplo controlado assistido por IA, não qualidade geral de respostas.
- Uma chamada **real** ao Ollama com `qwen2.5:3b` gerou uma explicação coerente
  sobre RAG e citou `[P2-T1]`. Levou **133,11 segundos**; a verificação do conteúdo
  foi assistida por IA e não substitui revisão humana.
- O `.env` local foi preparado para esse Ollama, com timeout de 180 segundos.
  Selecione **Resposta com IA** para usá-lo. A busca simples continua disponível.
- Gemini permanece como alternativa implementada, sem chamada real validada.
- O piloto com `llama3.2:1b` foi mais rápido (25,081 s), porém recusou a mesma
  pergunta apesar de a resposta constar do contexto. Mantivemos Qwen localmente.
  Não se trata de uma comparação controlada entre modelos.
- Avaliação com apostila real, revisão humana, gravação e edição do vídeo e
  preparação dos slides finais ainda precisam ser feitas.

## Conectar Gemini

Se aparecer “Não foi possível conectar ao provedor”, verifique a conexão do
processo que executa o aplicativo. Em 17/11, o servidor iniciado no ambiente
isolado de desenvolvimento teve acesso externo bloqueado (WinError 10013).
Reiniciá-lo com acesso à rede permitido resolveu o alcance do endpoint.
Uma falha de conexão anterior à autenticação não comprova chave inválida.

Para iniciar diretamente no seu terminal do VS Code, na pasta do projeto:

```powershell
& '.\.tools\python\python.exe' -m streamlit run app.py
```

A chave é carregada automaticamente da configuração privada do servidor. A
interface mostra apenas seu estado — definida ou ausente — e não oferece campo
de senha para digitá-la. A consulta de modelos remove espaços nas extremidades
da chave e informa se há espaços ou quebras de linha no meio, sem expor o valor.

Obtenha uma chave na sua conta do [Google AI Studio](https://aistudio.google.com/apikey).
Não cole a chave no chat nem a inclua em arquivos compartilhados.

Se o arquivo `.env` ainda não existir, crie a configuração privada a partir do
exemplo, sem sobrescrever um arquivo já configurado:

```powershell
if (-not (Test-Path -LiteralPath .env)) {
    Copy-Item -LiteralPath .env.example -Destination .env
}
```

Edite o `.env` privado do projeto no seu editor. Defina `LLM_PROVIDER=gemini`
e preencha `GEMINI_API_KEY` nesse arquivo, nunca no chat ou no código-fonte
compartilhável. `LLM_MODEL` é opcional até você consultar e escolher um modelo.
Provedor e seleção de modelo continuam disponíveis na interface; o botão
**Consultar modelos disponíveis** ajuda a obter o identificador. A consulta
envia a chave ao provedor, mas não envia o documento e não faz geração.

Salve o arquivo e atualize a página. O `.env` é relido a cada reexecução do
aplicativo, sem precisar reiniciar o servidor. Variáveis definidas explicitamente
no ambiente do processo têm prioridade sobre o arquivo; nesse caso, editar o
`.env` não substitui o valor dessas variáveis. A interface não revela a chave.

Antes de enviar a pergunta, marque a autorização. O aplicativo envia **apenas
a pergunta, o prompt de sistema e até três trechos recuperados**, não o PDF
inteiro. Os trechos ainda podem conter dados pessoais. A política de uso dos
dados e os custos do serviço dependem do provedor e da conta. Não há promessa
de gratuidade. Para resumir com Gemini, há uma autorização separada e específica
para enviar todo o texto extraído do intervalo selecionado; a autorização da
pergunta não substitui a do resumo.

As chamadas usam o endpoint REST `generateContent`. O prompt está em
`src/estudapdf/prompts.py`; não há dependência de um framework de agentes.


## Arquitetura e técnica de IA

A interface foi redesenhada em 17/11/2026, com workspace de consulta, painel
de evidências, envio de PDF no centro da página e, na barra lateral, a lista
de materiais estudados na sessão com o progresso de revisão de cada um
(somente em memória, sem gravação em disco). O ponto de
entrada é `app.py`; a implementação visual está em `frontend.py`, `ui.py`
e `assets/styles.css`. Não há dependência de fontes ou imagens externas.

```text
PDF → extração por página → trechos com sobreposição → índice TF-IDF
Pergunta → vetor TF-IDF → similaridade do cosseno → até 3 trechos
Pergunta + trechos + instruções → Gemini ou Ollama → resposta + evidências
```

- Extração local por `pypdf`, sem OCR.
- Trechos de até 1.100 caracteres com sobreposição de até 180, por página.
- TF-IDF com palavras e pares de palavras, normalização de acentos e frequência
  sublinear. Recuperação **lexical**, sem embeddings semânticos.
- Até três trechos, similaridade mínima operacional de 0,05. Esse limiar não foi
  calibrado e pode falhar; o score não é uma probabilidade de correção.
- O modelo é orientado a responder com base no contexto, citar IDs e reconhecer
  lacunas. Referências inexistentes no formato esperado fazem a resposta ser
  retida. Referências válidas ainda podem sustentar interpretações erradas.
- Não há treinamento de classificador ou ajuste dos pesos do modelo generativo.
- Sem evidência recuperada, não há chamada ao modelo.

## Limites e privacidade

- Um documento por vez, até 15 MB, 150 páginas e 1,5 milhão de caracteres
  extraídos. Há também um limite operacional de conteúdo interno por página.
  Esses limites não constituem isolamento contra PDFs maliciosos.
- PDFs protegidos e documentos sem texto selecionável são rejeitados.
- Tabelas, colunas e layouts complexos podem perder estrutura na extração.
- Sinônimos, palavras comuns ou perguntas vagas podem prejudicar a busca.
- Instruções em documentos são tratadas como dados não confiáveis; o prompt
  não garante proteção completa contra injeção de instruções.
- O aplicativo não grava documentos ou consultas automaticamente no disco e
  não usa cache global de documentos. Os dados ficam no estado da sessão.
- Limpar a sessão remove referências no app, sem promessa de limpeza forense
  da memória nem exclusão de dados eventualmente processados pelo provedor.
- O registro JSON baixado contém pergunta, evidências, prompt e resposta.
  Compartilhe somente material autorizado. O arquivo não contém a chave.
- Esta é uma ferramenta de apoio ao estudo. Conferir o material original é
  necessário; citações não garantem correção.

## Verificação e avaliação

```powershell
& '.\.tools\python\python.exe' verificar.py
& '.\.tools\python\python.exe' -m pip check
& '.\.tools\python\python.exe' avaliar.py --saida output/avaliacao-busca.json
```

`verificar.py` executa testes de extração real em PDF de memória, limites,
recuperação, interface Streamlit, orquestração e protocolos dos provedores.
Os testes HTTP usam respostas simuladas **apenas nos testes**; não comprovam
acesso real a uma conta Gemini ou disponibilidade de um modelo local.

`avaliar.py` testa dez perguntas no texto interno. Oito têm seção de referência;
duas pedem informação ausente. Sem `--gerar`, mede somente recuperação,
sem consumir API. O registro original fica em `output/avaliacao-demo.json`.
O programa não sobrescreve resultados: use outro nome para novas execuções.

Para avaliar respostas reais, depois de configurar e conferir o provedor:

```powershell
& '.\.tools\python\python.exe' avaliar.py --gerar --saida output/avaliacao-geracao.json
```

Esse comando faz até dez chamadas reais e pode consumir cota/créditos.
Revisão humana das respostas continua necessária. Veja `docs/AVALIACAO.md`.
O desempenho no exemplo interno não comprova eficácia em apostilas reais.

## Instalar em outro computador

Com Python 3.12 disponível:

```powershell
py -3.12 -m venv .venv
& '.\.venv\Scripts\python.exe' -m pip install -r requirements-lock.txt
& '.\.venv\Scripts\python.exe' -m streamlit run app.py
```

`requirements-lock.txt` registra o ambiente validado no Windows com Python 3.12;
`requirements.txt` registra faixas de dependências diretas. Para outros sistemas
ou versões, pode ser necessário resolver dependências a partir desse arquivo.
O comando `python verificar.py` funciona após instalar as dependências.

## Materiais da entrega

| Arquivo | Conteúdo |
| --- | --- |
| `docs/RELATORIO.md` | Rascunho do relatório; resultados empíricos pendentes são identificados |
| `docs/ARQUITETURA.md` | Diagrama e decisões técnicas |
| `docs/AVALIACAO.md` | Método, casos e distinção entre testes e validação real |
| `docs/APRESENTACAO.md` | Conteúdo proposto para oito slides, ainda em Markdown |
| `docs/ROTEIRO_VIDEO.md` | Roteiro de aproximadamente dez minutos; gravação e edição pelo grupo |
| `docs/PLANO_ENTREGA.md` | Cronograma e checklist |
| `docs/USO_DE_IA.md` | Registro de assistência e revisão a completar |

Código e rascunhos não substituem o vídeo, a apresentação e a revisão humana.
O relatório e os slides precisam refletir o que for efetivamente executado.

Para gerar um ZIP do código e materiais compartilháveis:

```powershell
& '.\.tools\python\python.exe' empacotar.py
```

O pacote exclui `.env`, o runtime, caches, PDFs e consultas particulares.
Inclui somente os registros conhecidos da demonstração educativa (recuperação,
pilotos de perguntas e resumo local) e as capturas da interface com esse
material. Registros de tentativa rejeitada são identificados como erro.
Revise o pacote antes da entrega e acrescente apenas resultados autorizados.

## Referências

- [Streamlit](https://docs.streamlit.io/)
- [Extração de texto com pypdf](https://pypdf.readthedocs.io/en/stable/user/extract-text.html)
- [Extração de características no scikit-learn](https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction)
- [Gemini generateContent](https://ai.google.dev/api/generate-content)
- [Ollama chat](https://docs.ollama.com/api/chat)

Código, material demonstrativo, planejamento e documentação produzidos com
assistência de Codex. Registrar revisores e alterações efetivas antes de entregar.
