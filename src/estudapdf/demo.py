"""Material educativo autoral de demonstração, assistido por IA; não é uma apostila real."""

from .document import Page

DEMO_NAME = "Guia demonstrativo de IA — texto educativo"

DEMO_SECTIONS = [
    """Aprendizado supervisionado e não supervisionado
No aprendizado supervisionado, o algoritmo aprende a partir de exemplos com
rótulos ou respostas de referência. Classificar mensagens como spam ou não spam
é um exemplo de classificação supervisionada. Na regressão, o alvo é um valor
numérico, como o preço de um imóvel. No aprendizado não supervisionado, os
exemplos não possuem uma resposta-alvo fornecida para cada observação. Uma
tarefa comum é o agrupamento: reunir observações semelhantes e explorar padrões.
Separar treino e teste ajuda a avaliar se o modelo generaliza para dados que
não foram utilizados no ajuste. O conjunto de teste deve permanecer separado
das decisões de treinamento. Uma boa pontuação em uma amostra pequena não
garante bom desempenho em situações reais diferentes.""",
    """Como funciona a geração aumentada por recuperação
RAG é a sigla de Retrieval-Augmented Generation, ou geração aumentada por
recuperação. O processo combina a busca de evidências em uma base documental
com a geração de uma resposta por um modelo de linguagem. Primeiro o documento
é dividido em trechos. A pergunta é comparada aos trechos e os mais relevantes
são recuperados. Em seguida, esses trechos são incluídos no contexto enviado
ao modelo, que deve fundamentar sua resposta nessas evidências. Esse fluxo não
treina nem altera os pesos do modelo de linguagem. RAG pode ajudar a localizar
informações de um material específico, mas não elimina respostas sem fundamento.
Se a recuperação falhar ou o trecho for insuficiente, o modelo pode errar.
É necessário conferir as evidências e reconhecer informação ausente.""",
    """TF-IDF, similaridade do cosseno e recuperação lexical
TF-IDF representa um texto por pesos associados aos termos presentes em uma
coleção. TF se relaciona à frequência de um termo no texto; IDF reduz o peso
de termos comuns em muitos textos da coleção. A similaridade do cosseno compara
a direção dos vetores. No EstudaPDF, vetores normalizados permitem calcular a
similaridade por produto escalar. Os trechos com maior similaridade lexical
com a pergunta são candidatos a contexto. A busca utiliza palavras e pares de
palavras, com normalização de acentos. Ela não é uma busca semântica com um
modelo de embeddings. Perguntas com sinônimos ou pouco vocabulário em comum
podem deixar de recuperar o trecho correto. O score de similaridade não mede
a veracidade da resposta nem é uma probabilidade calibrada de relevância.""",
    """Avaliação e limites de um assistente documental
Para avaliar um assistente, prepare perguntas e respostas de referência antes
de consultar o sistema. Registre os trechos esperados e onde eles aparecem.
Confira separadamente se a recuperação encontrou a informação, se a resposta
é sustentada pelo contexto e se as referências indicam as fontes corretas.
Inclua perguntas cuja resposta está ausente do material e perguntas formuladas
com sinônimos. Meça tempos somente durante execução real e registre erros.
Uma referência existente não prova que a afirmação é verdadeira: o trecho
precisa realmente sustentá-la. Documentos podem conter erros ou instruções
maliciosas. Trate seu conteúdo como dados não confiáveis. Use documentos
autorizados e evite enviar informações pessoais a serviços externos. Este
material não informa preços de APIs, versões de modelos ou datas de provas.""",
]


def demo_pages() -> list[Page]:
    return [Page(number=i, text=text, location_label="Seção") for i, text in enumerate(DEMO_SECTIONS, start=1)]
