import spacy

_nlp = None

def get_nlp():
    global _nlp
    if _nlp is None:
        # Singleton (lazy initialization): cria apenas um único objeto spaCy e reutiliza depois.
        # Como é usado: evita recarregar o modelo NLP várias vezes e mantém a instância compartilhada.
        try:
            _nlp = spacy.load("pt_core_news_md")
        except OSError:
            raise Exception(
                "Modelo pt_core_news_md não encontrado.\n"
                "Execute: python -m spacy download pt_core_news_md"
            )
    return _nlp

def analisar_texto(texto):
    nlp = get_nlp() 

    doc = nlp(texto)

    tokens = [
        token.lemma_.lower()
        for token in doc
        if not token.is_stop
        and not token.is_punct
    ]

    entidades = [
        {"texto": ent.text, "tipo": ent.label_}
        for ent in doc.ents
    ]

    return {
        "doc": doc,
        "tokens": tokens,
        "entidades": entidades
    }