# Imagem base do Python
FROM python:3.11-slim

# Variáveis para evitar arquivos desnecessários
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    netcat-openbsd

# Copiar requirements
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Baixa o modelo do SpaCy durante o build
RUN python -m spacy download pt_core_news_md

# Copiar código do projeto
COPY . .

# Copiar entrypoint
COPY entrypoint.sh /entrypoint.sh

# Dar permissão de execução
RUN chmod +x /entrypoint.sh

# Porta do Django
EXPOSE 8000

# Entry point (onde roda migrate + server)
ENTRYPOINT ["/entrypoint.sh"]