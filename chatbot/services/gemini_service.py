import os
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def chamar_api_chat(prompt):
    model = genai.GenerativeModel("gemini-1.5-flash")
    resposta = model.generate_content(prompt)
    return resposta.text