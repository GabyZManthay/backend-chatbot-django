import os
import spacy


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


# -------------------------
# CONVERSAS
# -------------------------

class ConversaViewSet(viewsets.ModelViewSet):

    queryset = Conversa.objects.all().order_by('-id_conversa')
    serializer_class = ConversaSerializer


# -------------------------
# ENDPOINT PRINCIPAL DO CHAT
# -------------------------

from rest_framework.views import APIView

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class PerguntarAPIView(APIView):

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['texto'],
            properties={
                'texto': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Texto da pergunta ao chatbot'
                )
            }
        ),
        responses={
            200: openapi.Response(
                description='Resposta do chatbot',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'conversa_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'pergunta': openapi.Schema(type=openapi.TYPE_STRING),
                        'resposta': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            )
        }
    )

    def post(self, request):

        serializer = PerguntarSerializer(
            data=request.data
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        if not base_manager.carregado:
            base_manager.carregar(CAMINHO_BASE)


        texto = serializer.validated_data["texto"]


        # Usuário anônimo
        usuario, _ = Usuario.objects.get_or_create(
            email="anonimo@chatbot.local",
            defaults={"nome": "Usuário Anônimo"}
        )
       
        # 1. NLP primeiro (para ter a intenção e resposta)
        resultado_nlp = analisar_texto(texto)
        intencao = identificar_intencao(texto)
        busca = base_manager.buscar(resultado_nlp["doc"])
        resposta_texto = formatar_resposta(busca)


        # 2. Cria PERGUNTA (sem conversa, porque Pergunta não tem FK para Conversa)
        pergunta = Pergunta.objects.create(
            descricao_pergunta=texto  
        )


        # 3. Cria RESPOSTA (sem pergunta, porque Resposta não tem FK para Pergunta)
        resposta = Resposta.objects.create(
            intencao=intencao.get("intencao", "GERAL"),  
            texto_resposta=resposta_texto,                
            tempo_resposta=None                          
        )


        # 4. Cria CONVERSA vinculando TUDO (porque Conversa tem as FKs)
        conversa = Conversa.objects.create(
            usuario=usuario,          
            pergunta=pergunta,        
            resposta=resposta,        
            avaliacao=None            
        )


        # 5. Retorna a resposta da API
        return Response({
            "conversa_id": conversa.id_conversa,
            "pergunta": pergunta.descricao_pergunta,  
            "resposta": resposta.texto_resposta        
        })

        

