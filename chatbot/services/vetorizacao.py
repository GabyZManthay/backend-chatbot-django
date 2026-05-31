from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from chatbot.models import Chunk
import numpy as np


# modelo de embedding
modelo = None


def get_modelo():
    global modelo

    if modelo is None:
        # Singleton (lazy initialization): instancia o modelo de embeddings uma vez.
        # Como é usado: garante que todas as buscas e vetorização usem a mesma instância de SentenceTransformer.
        modelo = SentenceTransformer(
            'all-MiniLM-L6-v2'
        )

    return modelo


# ------------------------------------------------
# EXTRAI TEXTO DO PDF
# ------------------------------------------------
def extrair_texto_pdf(caminho_pdf):

    reader = PdfReader(caminho_pdf)

    texto = ""

    for pagina in reader.pages:

        conteudo = pagina.extract_text()

        if conteudo:
            texto += conteudo

    return texto


# ------------------------------------------------
# DIVIDE TEXTO EM CHUNKS
# ------------------------------------------------
def dividir_chunks(
    texto,
    tamanho=1300,
    sobreposicao=200
):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=tamanho,
        chunk_overlap=sobreposicao,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            ""
        ]
    )

    chunks = splitter.split_text(texto)

    print(
        f"✅ Texto dividido em {len(chunks)} chunks inteligentes"
    )

    return chunks


# ------------------------------------------------
# PROCESSA DOCUMENTO
# ------------------------------------------------
def processar_documento(documento):

    print("📄 Processando documento...")

    caminho_pdf = documento.arquivo.path

    texto = extrair_texto_pdf(
        caminho_pdf
    )

    lista_chunks = dividir_chunks(
        texto
    )

    vetores = get_modelo().encode(
        lista_chunks
    )

    for i, chunk_texto in enumerate(
        lista_chunks
    ):

        Chunk.objects.create(
            conteudo=chunk_texto,
            ordem=i,
            documento=documento,
            vetor=vetores[i].tolist()
        )

    print(
        "✅ Documento vetorizado com sucesso!"
    )


# ------------------------------------------------
# BUSCA RAG COM FONTE DO PDF
# ------------------------------------------------
def buscar_chunks_rag(
    pergunta,
    top_k=10,
    score_minimo=0.40
):

    if not Chunk.objects.exists():
        return []

    vetor_pergunta = get_modelo().encode(
        pergunta
    )

    # ALTERAÇÃO AQUI:
    # agora buscamos documento__nome
    chunks_qs = list(
        Chunk.objects.select_related(
            'documento'
        ).values(
            'id_chunk',
            'conteudo',
            'vetor',
            'documento__nome'
        )
    )

    if not chunks_qs:
        return []

    chunk_vectors = np.array([
        c['vetor']
        for c in chunks_qs
    ])

    # similaridade cosseno
    norm_chunks = (
        chunk_vectors /
        np.linalg.norm(
            chunk_vectors,
            axis=1,
            keepdims=True
        )
    )

    norm_pergunta = (
        vetor_pergunta /
        np.linalg.norm(vetor_pergunta)
    )

    scores = np.dot(
        norm_chunks,
        norm_pergunta
    )

    relevantes = [
        (i, scores[i])
        for i in range(len(scores))
        if scores[i] >= score_minimo
    ]

    relevantes.sort(
        key=lambda x: x[1],
        reverse=True
    )

    print(
        f"🔍 Encontrados {len(relevantes)} chunks relevantes"
    )

    # ALTERAÇÃO PRINCIPAL:
    # agora retorna chunk + pdf + score
    resultados = []

    for i, score in relevantes[:top_k]:

        resultados.append({
            "conteudo":
                chunks_qs[i]['conteudo'],

            "documento":
                chunks_qs[i][
                    'documento__nome'
                ],

            "score":
                round(
                    float(score),
                    4
                )
        })

    return resultados