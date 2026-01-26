import os
import sys
from dotenv import load_dotenv

# Intentamos importar la nueva librería de Google
try:
    from google import genai
    print("✅ Librería 'google-genai' detectada correctamente.")
except ImportError:
    print("❌ ERROR: La librería no está instalada. Ejecuta: python -m pip install google-genai")
    sys.exit()

# 1. Cargar el archivo .env desde la raíz (TESIS...)
if load_dotenv():
    print("✅ Archivo .env cargado con éxito.")
else:
    print("⚠️ ADVERTENCIA: No se encontró el archivo .env o está en el lugar equivocado.")

# 2. Obtener la llave desde el archivo .env de forma segura
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ ERROR: La variable GOOGLE_API_KEY no existe en el archivo .env.")
else:
    try:
        # 3. Configurar el cliente con la llave recuperada
        client = genai.Client(api_key=api_key)
        print("✅ CONEXIÓN EXITOSA CON GOOGLE")
        
        print("--- LISTADO DE MODELOS DISPONIBLES ---")
        for model in client.models.list():
            print(f"-> {model.name}")
            
    except Exception as e:
        print(f"❌ Error al conectar: {e}")