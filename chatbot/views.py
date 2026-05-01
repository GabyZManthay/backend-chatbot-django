import os
import spacy
from chatbot.services.vetorizacao import buscar_chunks_rag
from chatbot.services.gemini_service import chamar_api_chat

from nlp.nlp import analisar_texto
from nlp.identificacao import identificar_intencao
from nlp.base_conhecimento import base_manager
from nlp.busca import formatar_resposta


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


CAMINHO_BASE = os.path.join(
    BASE_DIR,
    "../nlp/dados/edital.txt"
)


from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Documento
from .serializers import DocumentoSerializer

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema


from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from django.utils import timezone

from .models import Usuario
from .serializers import UsuarioSerializer

from .serializers import PerguntarSerializer

from .models import Pergunta, Conversa, Resposta
from .serializers import (
    PerguntaSerializer,
    ConversaSerializer,
    RespostaSerializer
)
from chatbot.services.vetorizacao import processar_documento



class DocumentoViewSet(viewsets.ModelViewSet):
    queryset = Documento.objects.all()
    serializer_class = DocumentoSerializer
    parser_classes = (MultiPartParser, FormParser)
    def perform_create(self, serializer):

        documento = serializer.save()

        # 🚀 roda vetorização automática
        processar_documento(documento)


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

    # 🔐 LOGIN
    @action(detail=False, methods=['post'])
    def login(self, request):

        email = request.data.get("email")
        senha = request.data.get("senha")

        try:
            usuario = Usuario.objects.get(email=email)

            if usuario.check_senha(senha):

                usuario.ultimo_acesso = timezone.now()
                usuario.save()

                return Response({
                    "mensagem": "Login realizado com sucesso",
                    "usuario": usuario.nome,
                })

            else:

                return Response({
                    "erro": "Senha incorreta"
                }, status=status.HTTP_401_UNAUTHORIZED)

        except Usuario.DoesNotExist:

            return Response({
                "erro": "Usuário não encontrado"
            }, status=status.HTTP_404_NOT_FOUND)


# -------------------------
# PERGUNTAS
# -------------------------

class PerguntaViewSet(viewsets.ModelViewSet):

    queryset = Pergunta.objects.all().order_by('-id_pergunta')
    serializer_class = PerguntaSerializer

    from chatbot.services.vetorizacao import buscar_chunks_rag  # ← Adicione no topo do arquivo

    # Sobrescreve o método de criação
    def create(self, request, *args, **kwargs):
        # Verifica se a requisição veio com o campo 'texto' (Chatbot)
        if "texto" in request.data:
            return self._criar_via_chatbot(request)
        
        # Se não tiver 'texto', cria normalmente (via Swagger normal)
        return super().create(request, *args, **kwargs)

    # def create(self, request, *args, **kwargs):
    #     # ✅ Exige estritamente o campo 'texto'
    #     if "texto" not in request.data or not request.data.get("texto"):
    #         return Response(
    #             {"erro": "Campo 'texto' é obrigatório."},
    #             status=status.HTTP_400_BAD_REQUEST
    #         )

    #     # ✅ Rota direta para o chatbot. Remove o fallback para criação manual.
    #     return self._criar_via_chatbot(request)

    def _criar_via_chatbot(self, request):
        """Lógica do Chatbot com RAG PDF + fallback NLP"""
        
        texto = request.data.get("texto")
        if not texto:
            return Response({"erro": "Campo 'texto' é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        usuario, _ = Usuario.objects.get_or_create(
            email="anonimo@chatbot.local",
            defaults={"nome": "Usuário Anônimo"}
        )
    
        #  1. Tenta buscar no PDF vetorizado (RAG)
        context_chunks = buscar_chunks_rag(texto, top_k=3, score_minimo=0.40)
        
        if context_chunks:
            contexto_rag = "\n\n".join(context_chunks)

            prompt = f"""
        Você é um assistente que responde perguntas usando APENAS o contexto abaixo.

        Contexto:
        {contexto_rag}

        Pergunta:
        {texto}

        Regras:
        - Responda de forma objetiva
        - Se houver número, informe claramente
        - Se não encontrar, diga que não encontrou
        """

            try:
                resposta_texto = chamar_api_chat(prompt)

            except Exception:
                resposta_texto = contexto_rag[:1500] 
            intencao_saida = "RAG_GPT"
            
        else:
            #  Fallback: usa NLP tradicional com edital.txt
            print(f" Sem chunks relevantes. Usando NLP tradicional para: '{texto}'")
            
            if not base_manager.carregado:
                base_manager.carregar(CAMINHO_BASE)
            
            resultado_nlp = analisar_texto(texto)
            intencao = identificar_intencao(texto)
            busca = base_manager.buscar(resultado_nlp["doc"])
            resposta_texto = formatar_resposta(busca)
            
            # Fallback final se não encontrar nada
            if not resposta_texto or len(resposta_texto.strip()) < 30:
                resposta_texto = " Não encontrei informações sobre isso nos documentos disponíveis. Tente reformular a pergunta."
            
            intencao_saida = intencao.get("intencao", "GERAL")

        # Cria os registros no banco
        pergunta = Pergunta.objects.create(descricao_pergunta=texto)
        resposta = Resposta.objects.create(
            intencao=intencao_saida,
            texto_resposta=resposta_texto,
            tempo_resposta=None
        )
        conversa = Conversa.objects.create(
            usuario=usuario,
            pergunta=pergunta,
            resposta=resposta,
            avaliacao=None
        )

        return Response({
            "id_pergunta": pergunta.id_pergunta,
            "conversa_id": conversa.id_conversa,
            "pergunta": pergunta.descricao_pergunta,
            "resposta": resposta.texto_resposta
        }, status=status.HTTP_201_CREATED)


# -------------------------
# CONVERSAS
# -------------------------

class ConversaViewSet(viewsets.ModelViewSet):

    queryset = Conversa.objects.all().order_by('-id_conversa')
    serializer_class = ConversaSerializer
