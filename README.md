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

1. **Regras locais** (`signals.py`): 10 padrões de alerta — pedido de Pix,
   código ou senha, link, urgência, troca de número, prêmio, taxa antecipada,
   instalação de aplicativo, dados pessoais e nome de instituição — e 1 sinal
   de legitimidade (mandar usar o aplicativo oficial, sem link nem pedido de
   dados). Funcionam sem internet e geram uma pontuação de 0 a 100.
2. **Catálogo de golpes + busca** (`catalog.py`, `retrieval.py`): 16 golpes
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

O conjunto `avaliacao/mensagens.json` tem 22 golpes e 14 mensagens legítimas,
fictícios e escritos a partir de alertas públicos, mais uma mensagem legítima
real (aviso de fatura do Nubank) que gerou um alarme falso e foi corrigida.
Resultado em 18/11/2026 com `gemini-3.5-flash-lite` e modelos reserva:

| | Só regras locais | Com IA |
| --- | --- | --- |
| Golpes detectados | 11/22 | 22/22 |
| Tipo de golpe correto | 9/11 | 22/22 |
| Alarmes falsos | 1/14 | 0/14 |
| Acurácia | 24/36 | 36/36 |
| Tempo médio | < 0,1 s | 5,4 s |

O conjunto é pequeno e foi escrito quase todo pelo próprio grupo: o resultado
demonstra funcionamento, não desempenho garantido em mensagens reais.

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
