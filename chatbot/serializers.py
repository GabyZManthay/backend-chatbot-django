from rest_framework import serializers
from .models import Documento
from .models import Pergunta
from .models import Conversa
from .models import Usuario
from django.contrib.auth.hashers import make_password
from .models import Pergunta, Resposta, Conversa

class DocumentoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Documento
        fields = '__all__'

        read_only_fields = (
            'data_insercao',
            'data_modificacao'
        )
                

class UsuarioSerializer(serializers.ModelSerializer):

    class Meta:
        model = Usuario
        fields = '__all__'

    def create(self, validated_data):
        senha = validated_data.pop('senha')

        usuario = Usuario(**validated_data)
        usuario.senha = make_password(senha)

        usuario.save()

        return usuario



class PerguntarSerializer(serializers.Serializer):

    texto = serializers.CharField(
        max_length=1000,
        help_text="Digite a pergunta do usuário"
    )

    chat_id = serializers.IntegerField(
        required=False,
        help_text="ID do chat/conversa existente (opcional)"
    )
    


class RespostaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resposta
        fields = [
            'id_resposta',
            'intencao',
            'texto_resposta',
            'tempo_resposta'
        ]


class PerguntaSerializer(serializers.ModelSerializer):

    texto = serializers.CharField(
        source='descricao_pergunta'
    )

    chat_id = serializers.SerializerMethodField()
    resposta = RespostaSerializer(read_only=True)

    class Meta:
        model = Pergunta
        fields = [
            'id_pergunta',
            'texto',
            'chat_id',
            'resposta'
        ]

    def get_chat_id(self, obj):
        if obj.conversa:
            return obj.conversa.id_conversa
        return None


class ConversaSerializer(serializers.ModelSerializer):

    usuario = serializers.SerializerMethodField()
    perguntas = PerguntaSerializer(many=True, read_only=True)

    class Meta:
        model = Conversa
        fields = [
            'id_conversa',
            'usuario',
            'data_conversa',
            'horario_conversa',
            'avaliacao',
            'perguntas'
        ]

    def get_usuario(self, obj):
        if obj.usuario:
            return {
                'id_usuario': obj.usuario.id_usuario,
                'nome': obj.usuario.nome,
                'email': obj.usuario.email
            }
        return None
        
        