import os
from datetime import datetime
from nlp.preprocessamento import normalizar_texto
from nlp.nlp import get_nlp
from nlp.nlp import get_nlp

class BaseConhecimentoManager:

    def __init__(self):
        self.sentencas = []
        self.docs = []
        self.metadata = []
        self.carregado = False
        self._nlp_model = None

    def carregar(self, caminho_arquivo):

        if not os.path.exists(caminho_arquivo):
            raise FileNotFoundError(
                f"Arquivo {caminho_arquivo} não encontrado."
            )

        print("🔄 Processando base...")

        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            texto = f.read()

        doc_base = get_nlp()(texto)

        self.sentencas.clear()
        self.docs.clear()
        self.metadata.clear()

        for i, sent in enumerate(doc_base.sents):

            texto_limpo = sent.text.strip()

            if texto_limpo:

                self.sentencas.append(texto_limpo)
                self.docs.append(sent)

                self.metadata.append({
                    "linha": i + 1,
                    "categoria": self._detectar_categoria(texto_limpo),
                    "data": datetime.now().isoformat()
                })

        self.carregado = True

        print(
            f"✅ {len(self.sentencas)} sentenças carregadas"
        )

    def _detectar_categoria(self, texto):
        """Detecta categoria priorizando frases específicas sobre palavras soltas"""
        texto_lower = texto.lower()
        
        # 🔹 PRIORIDADE 1: Frases exatas (mais específicas)
        if any(frase in texto_lower for frase in [
            "local das aulas", "campus colatina", "situado na", "avenida arino",
            "santa margarida", "colatina - es"
        ]):
            return "LOCAL"
        
        if any(frase in texto_lower for frase in [
            "inscrições começam", "terminam em", "dia 10 de março", "20 de março",
            "divulgado no site", "15 de abril"
        ]):
            return "DATA"
        
        if any(frase in texto_lower for frase in [
            "aulas serão ministras", "segunda a sexta", "19h às 22h", "bloco b"
        ]):
            return "HORARIO"
        
        if any(frase in texto_lower for frase in [
            "histórico escolar", "rg e cpf", "comprovante de residência",
            "documentos necessários"
        ]):
            return "DOCUMENTOS"
        
        if any(frase in texto_lower for frase in [
            "r$ 50", "taxa de inscrição", "boleto bancário", "valor da taxa"
        ]):
            return "CUSTO"
        
        if any(frase in texto_lower for frase in [
            "40 vagas", "curso de informática", "ampla concorrência", "cotistas"
        ]):
            return "VAGAS"
        
        # 🔹 PRIORIDADE 2: Palavras-chave genéricas (fallback)
        categorias = {
            "LOCAL": ["campus", "endereco", "sede", "onde", "bloco", "avenida", "cidade"],
            "DATA": ["prazo", "inicio", "final", "quando", "marco", "abril", "divulg"],
            "DOCUMENTOS": ["documento", "rg", "cpf", "historico", "comprovante"],
            "VAGAS": ["vaga", "curso", "quantas", "concorrencia", "cotista"],
            "CUSTO": ["valor", "preco", "taxa", "boleto", "pagamento"],
            "INSCRICAO": ["inscric", "matricul", "inscrever", "cadastro"],
            "HORARIO": ["horario", "hora", "segunda", "terca", "quarta", "19h", "22h"],
        }
        
        for cat, palavras in categorias.items():
            if any(p in texto_lower for p in palavras):
                return cat
        
        return "GERAL"

    def buscar(self, doc_pergunta):
        """
        Busca corrigida: Normaliza a pergunta e as frases do banco
        para ignorar acentos e letras maiúsculas.
        """
        
        if not self.carregado:
            return {"encontrou": False, "resposta": "Base não carregada."}

        # 1. Normaliza a pergunta do usuário
        pergunta_norm = normalizar_texto(doc_pergunta.text)
        
        # 2. Palavras-chave (TODAS sem acento!)
        palavras_chave = {
            "DATA": ["data", "prazo", "dia", "inicio", "final", "quando", "marco", "abril", "inscric", "matricul", "divulg"],
            "LOCAL": ["local", "campus", "endereco", "sede", "onde", "bloco", "avenida", "cidade", "colatina", "situado", "aula"],
            "DOCUMENTOS": ["documento", "rg", "cpf", "historico", "comprovante", "escolar", "residencia"],
            "VAGAS": ["vaga", "curso", "quantas", "disponivel", "oferta", "concorrencia", "cotista", "informatica"],
            "CUSTO": ["valor", "preco", "taxa", "gratuito", "custo", "boleto", "pagamento", "50", "real"],
            "INSCRICAO": ["inscric", "matricul", "inscrever", "cadastro", "registr"],
            "HORARIO": ["horario", "hora", "segunda", "terca", "quarta", "quinta", "sexta", "19h", "22h", "ministr"],
        }

        # 3. Detecta a intenção
        intencao_detectada = None
        for categoria, termos in palavras_chave.items():
            if any(termo in pergunta_norm for termo in termos):
                intencao_detectada = categoria
                break

        if not intencao_detectada:
            return {"encontrou": False, "resposta": "Não entendi a intenção da pergunta.", "confianca": 0}

        # 4. Busca a melhor frase
        termos_categoria = palavras_chave[intencao_detectada]
        melhor_idx = None
        melhor_pontos = -1

        for i, sent_text in enumerate(self.sentencas):
            sent_categoria = self.metadata[i]["categoria"]
            
            # IMPORTANTE: Normalizamos a frase do banco também!
            sent_norm = normalizar_texto(sent_text)
            
            if sent_categoria == intencao_detectada:
                # Conta quantas palavras-chave batem (comparando normalizado com normalizado)
                pontos = sum(1 for termo in termos_categoria 
                             if termo in pergunta_norm and termo in sent_norm)
                
                if pontos > melhor_pontos:
                    melhor_pontos = pontos
                    melhor_idx = i
        
        # 5. Retorna o resultado
        if melhor_idx is not None and melhor_pontos >= 1:
            return {
                "encontrou": True,
                "resposta": self.sentencas[melhor_idx], # Retorna a frase original (com acentos)
                "confianca": 0.75,
                "origem": f"linha {self.metadata[melhor_idx]['linha']}",
                "categoria": intencao_detectada
            }

        return {
            "encontrou": False,
            "resposta": "Não encontrei essa informação específica.",
            "confianca": 0
        }

# Singleton: instância única do gerenciador de conhecimento usada em todo o app.
# Como é usado: fornece um ponto global de acesso para buscar informações da base carregada.
base_manager = BaseConhecimentoManager()