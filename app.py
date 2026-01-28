import os
import csv
import json
from datetime import datetime
from dotenv import load_dotenv 
from google import genai 
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
CORS(app)

# --- CONFIGURACIÓN DE GEMINI SEGURA ---
api_key = os.getenv("GOOGLE_API_KEY")
# Usamos el cliente estándar para máxima compatibilidad con modelos experimentales
client = genai.Client(api_key=api_key)

system_instruction = """
Eres 'Morfolog-IA', un asistente experto en morfología verbal, aunque estás basado en un modelo algebraico de costo cognitivo no usarás explicaciones que involucren detalles del costo cognitivo.
Tu tono es académico, motivador y personalizado. Sin embargo, ten en cuenta que estás contestando a estudiantes de secundaria por lo que tus respuesta deben ser comprensibles y didácticas para un estudiante de tal nivel. 

REGLAS PEDAGÓGICAS ESTRICTAS:
1. FASE DE CONSULTA (Infinitivo): 
    - Identifica la categoría: Regular (R), Identidad (I-A), Sustitución (I-B) o Supleción (I-C).
    - Indica el significado en español del verbo y en qué contextos se utiliza en inglés.
    - NUNCA proporciones la conjugación en pasado o participio en esta fase.
    - Para esta fase brinda 3 ejemplos de uso del verbo en tiempo PRESENTE y tanto en inglés como en español.

2. FASE DE RETO (Validación):
    - Compara el intento del alumno con la forma correcta.
    - SI EL ALUMNO ACIERTA: 
      * "es_correcto": true.
      * En "explicacion_didactica": Felicítalo brevemente.
      * CAMPO "ejemplos": ES OBLIGATORIO incluir 3 oraciones. Usa el verbo conjugado en el tiempo solicitado por el usuario. 
      * Formato de oración: "Oración en inglés (Traducción al español)".
    - SI EL ALUMNO FALLA: 
      * "es_correcto": false.
      * En "explicacion_didactica": NO DES LA RESPUESTA. Analiza el error y da pistas con verbos similares.
      * CAMPO "ejemplos": Déjalo vacío [].

3. FORMATO DE SALIDA (JSON ESTRICTO):
    Responde ÚNICAMENTE con JSON. Si el alumno acierta ("es_correcto": true), el campo "ejemplos" NO PUEDE ESTAR VACÍO.
    {
      "es_correcto": true/false/null,
      "tipo_algoritmo": "(R) | (I-A) | (I-B) | (I-C)",
      "explicacion_didactica": "...",
      "ejemplos": ["Sentence 1 in English (Traducción 1)", "Sentence 2 in English (Traducción 2)"]
    }
"""

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/consultar_fase1', methods=['POST'])
def consultar_fase1():
    data = request.json
    verbo = data.get('verbo', '').strip().lower()
    
    try:
        response = client.models.generate_content(
            model="gemini-flash-latest", 
            config={
                'system_instruction': system_instruction,
                'temperature': 0.1
            },
            contents=f"Fase 1: Analiza el infinitivo '{verbo}'. No conjugues."
        )
        return procesar_y_guardar(verbo, "Consulta_Andamiaje", response.text)
    
    except Exception as e:
        print(f"Error de API: {e}")
        return jsonify({"error": "Límite de cuota alcanzado", "detalle": "Espera 60 segundos antes de reintentar."}), 429

@app.route('/validar_reto', methods=['POST'])
def validar_reto():
    data = request.json
    verbo = data.get('verbo', '').strip().lower()
    intento = data.get('intento', '').strip().lower()
    tiempo = data.get('tiempo', 'pasado simple')
    
    prompt = (
        f"Fase Reto: Verbo '{verbo}'. Intento del alumno para {tiempo}: '{intento}'. "
        f"Si el intento es correcto, genera obligatoriamente los 2 ejemplos en {tiempo} "
        f"dentro del campo 'ejemplos' del JSON."
    )
    
    try:
        response = client.models.generate_content(
            model="gemini-flash-latest",
            config={
                'system_instruction': system_instruction,
                'temperature': 0.1
            },
            contents=prompt
        )
        return procesar_y_guardar(verbo, f"Reto_{tiempo}", response.text, intento)
    
    except Exception as e:
        print(f"Error de API: {e}")
        return jsonify({"error": "Límite de cuota alcanzado", "detalle": "Espera 60 segundos antes de reintentar."}), 429

def procesar_y_guardar(verbo, fase, texto_raw, intento="N/A"):
    try:
        inicio = texto_raw.find('{')
        fin = texto_raw.rfind('}') + 1
        if inicio == -1 or fin == 0:
            raise ValueError("No se encontró un JSON válido en la respuesta")
        
        texto_limpio = texto_raw[inicio:fin]
        datos_json = json.loads(texto_limpio)
        
        nombre_archivo = 'datos_recoleccion_tesis.csv'
        archivo_existe = os.path.isfile(nombre_archivo)
        
        es_corr = datos_json.get("es_correcto")
        if es_corr is True: resultado_final = "Acierto"
        elif es_corr is False: resultado_final = "Error"
        else: resultado_final = "Consulta"
        
        fila = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            fase,
            verbo,
            intento,
            len(intento) if intento != "N/A" else 0,
            resultado_final,
            datos_json.get("tipo_algoritmo", "N/A")
        ]
        
        with open(nombre_archivo, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not archivo_existe:
                writer.writerow(["Timestamp", "Fase", "Verbo", "Input_Estudiante", "Longitud_Input", "Resultado", "Categoria_Algebraica"])
            writer.writerow(fila)
            
        return jsonify(datos_json)
        
    except Exception as e:
        print(f"Error en procesamiento: {e}")
        return jsonify({"error": "Error interno", "detalle": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)