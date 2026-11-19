# AlertaGolpe

**Detector de golpes em mensagens, com IA generativa e busca em catálogo.**
A pessoa cola uma mensagem suspeita de WhatsApp, SMS ou e-mail e o AlertaGolpe
mostra o nível de risco, os sinais de alerta (com o trecho exato da mensagem),
com qual golpe conhecido ela se parece e o que fazer agora.

Projeto acadêmico de IA Generativa, entrega em **19/11/2026**, grupo de cinco integrantes.

## Começar neste computador

Na pasta `D:\TrabalhoAI`, execute no PowerShell:

```powershell
& '.\.tools\python\python.exe' -m streamlit run app.py
```

Abra **http://127.0.0.1:8501**. Também existe `iniciar.ps1`.

## Como funciona

Três camadas independentes, combinadas no resultado:

1. **Regras locais** (`signals.py`): 11 padrões de alerta — pedido de Pix,
   código ou senha, link, urgência, troca de número, prêmio, taxa antecipada,
   instalação de aplicativo, dados pessoais, nome de instituição e pendência
   ou regularização — e 1 sinal
   de legitimidade (mandar usar o aplicativo oficial, sem link nem pedido de
   dados). Funcionam sem internet e geram uma pontuação de 0 a 100.
2. **Catálogo de golpes + busca** (`catalog.py`, `retrieval.py`): 30 golpes
   frequentes no Brasil, com fontes. A mensagem é comparada a eles por TF-IDF
   e similaridade do cosseno; os 3 mais parecidos vão para a IA como contexto
   (padrão RAG).
3. **IA generativa** (`analyzer.py`): o Gemini recebe a mensagem como dado não
   confiável, os sinais e os golpes candidatos, e devolve risco, resumo, sinais
   com trechos exatos e ações, em JSON.

O aplicativo **valida** a resposta: recusa golpes fora da lista de candidatos,
descarta sinais cujo trecho não existe na mensagem e avisa quando a IA e as
regras discordam muito. Sem chave da API, funciona só com as regras locais.

## Configurar o Gemini

Copie `.env.example` para `.env` e preencha:

```
GEMINI_API_KEY=sua-chave
LLM_MODEL=gemini-3.5-flash-lite
LLM_FALLBACK_MODELS=gemini-3.1-flash-lite,gemini-flash-lite-latest
```

A chave fica só no servidor: não aparece na interface, nos downloads nem no
repositório. Erros temporários do Gemini (HTTP 5xx) são repetidos até três
vezes; uma resposta em JSON quebrado é pedida de novo uma vez. Se o modelo
principal continuar sobrecarregado ou deixar de existir, o app tenta os
modelos reserva de `LLM_FALLBACK_MODELS`, em ordem, e mostra na tela qual
modelo respondeu. O limite de uso por minuto (429) também aciona o reserva,
pois é contado por modelo; erros de chave não trocam de modelo.

## Avaliação

```powershell
& '.\.tools\python\python.exe' avaliar.py          # regras locais e IA
& '.\.tools\python\python.exe' avaliar.py --local  # só regras locais
```

O conjunto `avaliacao/mensagens.json` tem 36 golpes e 20 mensagens legítimas,
quase todos fictícios e escritos a partir de alertas públicos. Duas mensagens
são reais, sem dados pessoais: um aviso de fatura do Nubank, que gerou um
alarme falso, e um e-mail de falsa regularização do MEI, que recebeu só risco
médio. Os dois erros foram corrigidos.
Resultado em 19/11/2026 com `gemini-3.5-flash-lite` e modelos reserva:

| | Só regras locais | Com IA |
| --- | --- | --- |
| Golpes detectados | 18/36 | 36/36 |
| Tipo de golpe correto | 16/18 | 36/36 |
| Alarmes falsos | 3/20 | 0/19 |
| Acurácia | 35/56 | 55/55 (+1 falha do serviço) |
| Tempo médio | < 0,1 s | 9,9 s |

Há também dois testes extras com mensagens inéditas: `avaliacao/teste-ajuste.json`
(56 mensagens, usado para encontrar falhas e ajustar o catálogo) e
`avaliacao/teste-reserva.json` (20 mensagens, não usado em nenhum ajuste; a IA
acertou as 20). Para rodar: `avaliar.py --conjunto avaliacao/teste-reserva.json`.

**Mensagens reais.** `src/alertagolpe/exemplos_reais.json` tem 18 mensagens de
golpe reais, copiadas de reportagens e alertas públicos (com a fonte), que
alimentam o catálogo. Outras 16 ficaram separadas para teste em
`avaliacao/reais-teste.json`: a IA acertou 15.

Os conjuntos são pequenos e foram escritos quase todos pelo próprio grupo: o
resultado demonstra funcionamento, não desempenho garantido em mensagens reais.

## Testes

```powershell
& '.\.tools\python\python.exe' -m unittest discover -s tests
```

56 testes automatizados (regras, catálogo, busca, validação da resposta da IA,
cliente HTTP e interface). As respostas da IA nos testes são simuladas.

## Limites e privacidade

- É um apoio, não uma garantia: golpes novos podem não estar no catálogo, e a
  IA pode errar nos dois sentidos. Na dúvida, confirme pelo canal oficial.
- Ao analisar com IA, a mensagem é enviada à API Gemini. A interface avisa
  isso e recomenda apagar dados pessoais antes de colar.
- O histórico fica só na sessão do navegador; nada é gravado em disco.

## Instalar em outro computador

Com Python 3.12:

```powershell
py -3.12 -m venv .venv
& '.\.venv\Scripts\python.exe' -m pip install -r requirements-lock.txt
& '.\.venv\Scripts\python.exe' -m streamlit run app.py
```

## Uso de IA no desenvolvimento

O código, os testes, o catálogo e a documentação foram produzidos com
assistência de IA (Codex e Claude Code) e precisam de revisão do grupo. O
registro detalhado está em `docs/USO_DE_IA.md`.
