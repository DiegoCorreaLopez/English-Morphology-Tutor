import os
import sys
from dotenv import load_dotenv

# Intentamos importar la nueva librería usando el nombre oficial del paquete
try:
    from google import genai
    print("--- Libreria google-genai detectada correctamente ---")
except ImportError:
    print("ERROR: No se detecta 'google-genai'. Intenta ejecutar: python -m pip install google-genai")
    sys.exit()

# 1. Cargar el archivo .env
if load_dotenv():
    print("--- Archivo .env cargado con exito ---")
else:
    print("ADVERTENCIA: No se encontro el archivo .env")

# 2. Obtener la llave
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("ERROR: No hay llave en el .env")
else:
    try:
        # 3. Configurar el cliente
        client = genai.Client(api_key=api_key)
        print("--- CONEXION EXITOSA CON GOOGLE ---")
        
        print("--- MODELOS PARA TU TESIS ---")
        for model in client.models.list():
            # Filtramos para ver solo los que te sirven (Gemini)
            if "gemini" in model.name:
                print(f"-> {model.name}")
            
    except Exception as e:
        print(f"Error al conectar: {e}")