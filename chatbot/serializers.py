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


class PerguntaSerializer(serializers.ModelSerializer):
    texto = serializers.CharField(source='descricao_pergunta')
    class Meta:
        model = Pergunta
        fields = '__all__'
        fields = ['texto']  


class RespostaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resposta
        fields = '__all__'


class ConversaSerializer(serializers.ModelSerializer):

    perguntas = PerguntaSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Conversa
        fields = '__all__'
        
        