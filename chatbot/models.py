from django.db import models
from django.contrib.auth.hashers import make_password, check_password


# -------------------------
# PERFIL DE ACESSO
# -------------------------



# -------------------------
# USUARIO
# -------------------------

class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)

    nome = models.CharField(max_length=100)
    email = models.CharField(max_length=150)
    senha = models.CharField(max_length=255)
    
    # NOVO CAMPO
    admin = models.BooleanField(
        default=False
    )

    data_cadastro = models.DateTimeField(auto_now_add=True)
    ultimo_acesso = models.DateTimeField(null=True, blank=True)

    def set_senha(self, senha):
        self.senha = make_password(senha)

    def check_senha(self, senha):
        return check_password(senha, self.senha)

    def __str__(self):
        return self.nome


# -------------------------
# PERGUNTA
# -------------------------

class Pergunta(models.Model):
    id_pergunta = models.AutoField(primary_key=True)

    descricao_pergunta = models.TextField()

    conversa = models.ForeignKey(
        'Conversa',
        on_delete=models.CASCADE,
        related_name='perguntas',
        null=True,
        blank=True
    )

    def __str__(self):
        return self.descricao_pergunta[:50]


# -------------------------
# RESPOSTA
# -------------------------

class Resposta(models.Model):
    id_resposta = models.AutoField(primary_key=True)
    intencao = models.CharField(max_length=100)
    texto_resposta = models.TextField()
    tempo_resposta = models.DurationField(null=True, blank=True)

    pergunta = models.OneToOneField(
        Pergunta,
        on_delete=models.CASCADE,
        related_name='resposta',
        null=True,
        blank=True
    )

    def __str__(self):
        return self.intencao


# -------------------------
# CATEGORIA
# -------------------------

class Categoria(models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nome_categoria = models.CharField(max_length=100)

    def __str__(self):
        return self.nome_categoria


# -------------------------
# DOCUMENTO
# -------------------------

from django.db import models
from django.utils import timezone


from django.db import models
from django.utils import timezone


class Documento(models.Model):
    id_documento = models.AutoField(primary_key=True)

    nome = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    arquivo = models.FileField(
        upload_to="documentos/",
        null=True,
        blank=True
    )

    data_insercao = models.DateTimeField(
        auto_now_add=True
    )

    # começa null
    data_modificacao = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return (
            self.nome
            if self.nome
            else f"Documento {self.id_documento}"
        )


# -------------------------
# CATEGORIA_DOCUMENTO
# -------------------------

class CategoriaDocumento(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE)


# -------------------------
# GERENCIADOR_DIALOGO
# -------------------------

class GerenciadorDialogo(models.Model):
    id_gerenciador = models.AutoField(primary_key=True)

    documento = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE
    )

    id_base = models.IntegerField()


# -------------------------
# CONVERSA
# -------------------------

class Conversa(models.Model):
    id_conversa = models.AutoField(primary_key=True)

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE
    )

    gerenciador = models.ForeignKey(
        GerenciadorDialogo,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # DATA AUTOMÁTICA
    data_conversa = models.DateField(
        auto_now_add=True
    )

    # HORA AUTOMÁTICA
    horario_conversa = models.TimeField(
        auto_now_add=True
    )

    avaliacao = models.BooleanField(
        null=True,
        blank=True
    )

# -------------------------
# EXPORTACAO
# -------------------------

class Exportacao(models.Model):
    id_exportacao = models.AutoField(primary_key=True)

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)

    chatbot = models.IntegerField()

    conversa = models.ForeignKey(
        Conversa,
        on_delete=models.CASCADE
    )


# -------------------------
# TOKENS
# -------------------------

class Token(models.Model):
    id_token = models.AutoField(primary_key=True)

    tipo = models.CharField(max_length=100)
    quantidade = models.IntegerField()
    modelo = models.CharField(max_length=100)
    custo = models.DecimalField(max_digits=10, decimal_places=4)

    criado_em = models.DateTimeField(auto_now_add=True)


# -------------------------
# CHUNKS
# -------------------------

class Chunk(models.Model):
    id_chunk = models.AutoField(primary_key=True)

    conteudo = models.TextField()

    ordem = models.IntegerField()

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    documento = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        related_name="chunks"
    )
    
    vetor = models.JSONField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"Chunk {self.id_chunk}"


# -------------------------
# VERSAO_DOCUMENTO
# -------------------------

class VersaoDocumento(models.Model):
    id_versao = models.AutoField(primary_key=True)

    documento = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE
    )

    numero_versao = models.IntegerField()

    conteudo = models.TextField()

    data_versao = models.DateField(auto_now_add=True)

    autor_alteracao = models.CharField(max_length=100)