import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env")

api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

print(f"Testing Gemini API...")
print(f"Model: {model_name}")
print(f"API Key present: {bool(api_key)}")

from langchain_google_genai import ChatGoogleGenerativeAI

try:
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=0.2
    )
    response = llm.invoke("Responde unicamente 'OK CONEXION EXITOSA' si recibes este mensaje.")
    print(f"Respuesta del modelo: {response.content}")
except Exception as e:
    print(f"Error conectando con Gemini: {e}")
