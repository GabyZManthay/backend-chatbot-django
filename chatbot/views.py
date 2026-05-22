import os
import spacy
from chatbot.services.vetorizacao import buscar_chunks_rag
from chatbot.services.gemini_service import chamar_api_chat
from chatbot.services.vetorizacao import processar_documento

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



from django.utils import timezone


from django.utils import timezone


from django.utils import timezone


class DocumentoViewSet(viewsets.ModelViewSet):
    queryset = Documento.objects.all()
    serializer_class = DocumentoSerializer
    parser_classes = (
        MultiPartParser,
        FormParser
    )

    def perform_create(self, serializer):

        documento = serializer.save()

        # POST -> data_modificacao fica null
        processar_documento(documento)

    def perform_update(self, serializer):

        # PATCH/PUT -> seta automaticamente
        documento = serializer.save(
            data_modificacao=timezone.now()
        )

        # reprocessa se trocar arquivo
        if "arquivo" in self.request.FILES:
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

    queryset = Pergunta.objects.all().order_by(
        '-id_pergunta'
    )

    serializer_class = PerguntaSerializer

    # ------------------------------------------------
    # CREATE
    # ------------------------------------------------
    def create(
        self,
        request,
        *args,
        **kwargs
    ):

        if "texto" in request.data:
            return self._criar_via_chatbot(
                request
            )

        return super().create(
            request,
            *args,
            **kwargs
        )

    # ------------------------------------------------
    # CHATBOT
    # ------------------------------------------------
    def _criar_via_chatbot(
        self,
        request
    ):

        texto = request.data.get(
            "texto"
        )

        chat_id = request.data.get(
            "chat_id"
        )

        if not texto:
            return Response(
                {
                    "erro":
                    "Campo 'texto' é obrigatório."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ----------------------------------------
        # usuário anônimo
        # ----------------------------------------
        usuario, _ = Usuario.objects.get_or_create(
            email="anonimo@chatbot.local",
            defaults={
                "nome":
                "Usuário Anônimo"
            }
        )

        # ----------------------------------------
        # CHAT OPCIONAL
        # ----------------------------------------
        if chat_id:

            try:

                conversa = Conversa.objects.get(
                    id_conversa=chat_id
                )

            except Conversa.DoesNotExist:

                return Response(
                    {
                        "erro":
                        "Chat não encontrado"
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

        else:

            conversa = Conversa.objects.create(
                usuario=usuario,
                avaliacao=None
            )

        # =====================================================
        # 1. BUSCA RAG
        # =====================================================

        context_chunks = buscar_chunks_rag(
            texto,
            top_k=20,
            score_minimo=0.30
        )

        fontes = []

        # =====================================================
        # 2. RAG + LLM
        # =====================================================

        if context_chunks:

            # monta contexto
            contexto_rag = "\n\n".join([
                chunk["conteudo"]
                for chunk in context_chunks
            ])

            # captura PDFs usados
            fontes = list(set([
                chunk["documento"]
                for chunk in context_chunks
            ]))

            print(
                "📚 Fontes encontradas:"
            )

            print(fontes)

            prompt = f"""
            Você é um assistente especialista
            em responder perguntas sobre editais.

            REGRAS IMPORTANTES:

            - Responda SOMENTE usando o contexto fornecido
            - Nunca invente informações
            - Nunca misture informações de documentos diferentes
            - Se houver respostas diferentes em PDFs diferentes,
            mostre TODAS separadamente
            - Associe corretamente cada resposta ao edital
            - Copie datas exatamente como aparecem
            - Seja objetivo
            - Se não encontrar a informação diga:
            "Não encontrei essa informação nos documentos."

            CONTEXTO:
            {contexto_rag}

            PERGUNTA:
            {texto}
            """

            print(
                "🚀 Enviando prompt para LLM..."
            )

            try:

                resposta_texto = chamar_api_chat(
                    prompt
                )

                print(
                    "✅ Resposta da LLM:"
                )

                print(
                    resposta_texto
                )

                intencao_saida = (
                    "RAG_GPT"
                )

            except Exception as e:

                print(
                    "❌ Erro ao chamar LLM:"
                )

                print(str(e))

                resposta_texto = (
                    "Erro ao gerar resposta."
                )

                intencao_saida = (
                    "RAG_GPT"
                )

        # =====================================================
        # 3. FALLBACK NLP
        # =====================================================

        else:

            print(
                f"📚 Sem chunks relevantes. "
                f"Usando NLP tradicional para: "
                f"'{texto}'"
            )

            if not base_manager.carregado:

                base_manager.carregar(
                    CAMINHO_BASE
                )

            resultado_nlp = analisar_texto(
                texto
            )

            intencao = identificar_intencao(
                texto
            )

            busca = base_manager.buscar(
                resultado_nlp["doc"]
            )

            resposta_texto = (
                formatar_resposta(
                    busca
                )
            )

            if (
                not resposta_texto
                or
                len(
                    resposta_texto.strip()
                ) < 30
            ):

                resposta_texto = (
                    "Não encontrei "
                    "informações sobre isso "
                    "nos documentos disponíveis. "
                    "Tente reformular "
                    "a pergunta."
                )

            intencao_saida = (
                intencao.get(
                    "intencao",
                    "GERAL"
                )
            )

        # =====================================================
        # 4. SALVA NO BANCO
        # =====================================================

        resposta = Resposta.objects.create(
            intencao=intencao_saida,
            texto_resposta=resposta_texto,
            tempo_resposta=None
        )

        pergunta = Pergunta.objects.create(
            descricao_pergunta=texto,
            conversa=conversa
        )

        # =====================================================
        # 5. RETORNO API
        # =====================================================

        return Response(
            {
                "id_pergunta":
                    pergunta.id_pergunta,

                "chat_id":
                    conversa.id_conversa,

                "pergunta":
                    pergunta.descricao_pergunta,

                "resposta":
                    resposta.texto_resposta
            },
            status=status.HTTP_201_CREATED
        )

# -------------------------
# CONVERSAS
# -------------------------

class ConversaViewSet(viewsets.ModelViewSet):

    queryset = Conversa.objects.all().order_by('-id_conversa')
    serializer_class = ConversaSerializer
