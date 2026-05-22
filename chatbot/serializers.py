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
        allow_null=True,
        help_text="ID do chat/conversa existente (opcional)"
    )
    


class PerguntaSerializer(serializers.ModelSerializer):

    texto = serializers.CharField(
        source='descricao_pergunta'
    )

    chat_id = serializers.SerializerMethodField()

    class Meta:
        model = Pergunta
        fields = [
            'id_pergunta',
            'texto',
            'chat_id'
        ]

    def get_chat_id(self, obj):
        if obj.conversa:
            return obj.conversa.id_conversa
        return None


class RespostaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resposta
        fields = '__all__'


class ConversaSerializer(serializers.ModelSerializer):

    class Meta:
        model = Conversa
        fields = '__all__'
        
        