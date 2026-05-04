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
        modelo = SentenceTransformer('all-MiniLM-L6-v2')
    return modelo


# Extrair texto do PDF
def extrair_texto_pdf(caminho_pdf):

    reader = PdfReader(caminho_pdf)

    texto = ""

    for pagina in reader.pages:

        conteudo = pagina.extract_text()

        if conteudo:
            texto += conteudo

    return texto


# Dividir texto em chunks
def dividir_chunks(texto, tamanho=300, sobreposicao=100):
    """Divide texto preservando parágrafos e evitando cortes em palavras"""
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=tamanho,
        chunk_overlap=sobreposicao,  # mantém contexto entre chunks
        separators=["\n\n", "\n", ". ", " ", ""]  # prioriza quebras naturais
    )
    
    chunks = splitter.split_text(texto)
    print(f"✅ Texto dividido em {len(chunks)} chunks inteligentes")
    return chunks



# 🧠 Pipeline completo
def processar_documento(documento):

    print("Processando documento...")

    caminho_pdf = documento.arquivo.path

    texto = extrair_texto_pdf(caminho_pdf)

    lista_chunks = dividir_chunks(texto)

    vetores = get_modelo().encode(lista_chunks)

    for i, chunk_texto in enumerate(lista_chunks):

        Chunk.objects.create(
            conteudo=chunk_texto,
            ordem=i,
            documento=documento,
            vetor=vetores[i].tolist()
        )

    print("Documento vetorizado com sucesso!")

def buscar_chunks_rag(pergunta, top_k=3, score_minimo=0.40):
    """Busca chunks relevantes com filtro de similaridade mínima"""

    if not Chunk.objects.exists():
        return []

    # 1. Embedding da pergunta
    vetor_pergunta = get_modelo().encode(pergunta)

    # 2. Recupera chunks do banco
    chunks_qs = list(Chunk.objects.values('id_chunk', 'conteudo', 'vetor'))
    if not chunks_qs:
        return []
    
    chunk_vectors = np.array([c['vetor'] for c in chunks_qs])

    # 3. Similaridade cosseno
    norm_chunks = chunk_vectors / np.linalg.norm(chunk_vectors, axis=1, keepdims=True)
    norm_pergunta = vetor_pergunta / np.linalg.norm(vetor_pergunta)
    scores = np.dot(norm_chunks, norm_pergunta)

    # 4. Filtra por score mínimo E pega top_k
    relevantes = [(i, scores[i]) for i in range(len(scores)) if scores[i] >= score_minimo]
    relevantes.sort(key=lambda x: x[1], reverse=True)
    
    print(f"🔍 Encontrados {len(relevantes)} chunks relevantes (score ≥ {score_minimo})")
    
    return [chunks_qs[i]['conteudo'] for i, _ in relevantes[:top_k]]