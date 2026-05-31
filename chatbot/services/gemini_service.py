#instanciar os objetos da open ia e colocar oque ta no .env

import os
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def chamar_api_chat(prompt):
    # Adapter: encapsula a API do Google Gemini e expõe uma interface simples.
    # Como é usado: traduz chamadas internas do app para a biblioteca externa google.generativeai.
    model = genai.GenerativeModel("gemini-2.5-flash")
    resposta = model.generate_content(prompt)
    return resposta.text