import base64
import json
import os
import functions_framework
from google.cloud import bigquery
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig

# ================= CONFIGURACIÓN =================
PROJECT_ID = "portfolio-sentiment-ai"  # Cambia por tu ID de proyecto
REGION = "us-central1"                # Región recomendada para Vertex AI
DATASET_ID = "reputacion_marca"
TABLE_ID = "comentarios_analizados"
# =================================================

# Inicializar los clientes globales de GCP (fuera de la función para optimizar rendimiento)
vertexai.init(project=PROJECT_ID, location=REGION)
bq_client = bigquery.Client(project=PROJECT_ID)
table_ref = bq_client.dataset(DATASET_ID).table(TABLE_ID)

@functions_framework.cloud_event
def procesar_comentario_con_ia(cloud_event):
    """Función gatillada por un evento de Pub/Sub."""
    
    # 1. Extraer y decodificar el mensaje de Pub/Sub
    try:
        pubsub_message = cloud_event.data["message"]
        if "data" not in pubsub_message:
            print("⚠️ Mensaje vacío recibido.")
            return
            
        data_bytes = base64.b64decode(pubsub_message["data"])
        data_json = json.loads(data_bytes.decode("utf-8"))
        
        id_mensaje = data_json.get("id_mensaje")
        texto_original = data_json.get("texto", "")
        print(f"📥 Procesando mensaje ID: {id_mensaje} | Texto: '{texto_original[:30]}...'")
        
    except Exception as e:
        print(f"❌ Error al decodificar el mensaje de Pub/Sub: {e}")
        return

    # 2. Configurar el prompt y llamar a Gemini
    try:
        model = GenerativeModel("gemini-2.5-flash")
        
        prompt = f"""
        Analiza el siguiente comentario de un cliente y clasifícalo según las instrucciones.
        Comentario: "{texto_original}"
        
        Debes responder EXCLUSIVAMENTE con un objeto JSON válido que contenga las siguientes llaves:
        - "sentimiento": Debe ser exactamente uno de estos valores: [Positivo, Neutral, Negativo, Extremadamente Negativo].
        - "score_sentimiento": Un número flotante entre -1.0 (muy negativo) y 1.0 (muy positivo).
        - "categoria": Debe ser exactamente uno de estos valores: [Falla técnica, Facturación, Servicio al cliente, Felicitación].
        - "resumen_gemini": Un extracto o resumen del problema/comentario de máximo 5 palabras.
        """
        
        # Forzar a Gemini a responder en formato JSON estructurado
        config = GenerationConfig(
            response_mime_type="application/json",
            temperature=0.1  # Baja temperatura para respuestas consistentes y deterministas
        )
        
        response = model.generate_content(prompt, generation_config=config)
        ia_insights = json.loads(response.text)
        
    except Exception as e:
        print(f"❌ Error en la llamada a Vertex AI (Gemini): {e}")
        return

    # 3. Preparar los datos e insertar en BigQuery
    try:
        # Determinar si requiere alerta crítica basándonos en las reglas de negocio
        sentimiento_final = ia_insights.get("sentimiento", "Neutral")
        score_final = ia_insights.get("score_sentimiento", 0.0)
        
        # Una alerta se marca si es extremadamente negativo o si hay un score muy bajo
        detona_alerta = True if (sentimiento_final == "Extremadamente Negativo" or score_final <= -0.7) else False

        # Construir la fila para BigQuery respetando el esquema SQL
        fila_a_insertar = [{
            "id_mensaje": id_mensaje,
            "texto_original": texto_original,
            "sentimiento": sentimiento_final,
            "score_sentimiento": score_final,
            "categoria": ia_insights.get("categoria", "General"),
            "resumen_gemini": ia_insights.get("resumen_gemini", ""),
            "alerta_enviada": detona_alerta
        }]
        
        # Insertar fila por streaming
        errores = bq_client.insert_rows_json(table_ref, fila_a_insertar)
        
        if errores == []:
            print(f"✅ Análisis guardado exitosamente en BigQuery para ID: {id_mensaje}")
            if detona_alerta:
                print(f"🚨 [ALERTA] Se detectó un caso crítico para el ID {id_mensaje}. Enviar notificación.")
        else:
            print(f"❌ Errores al insertar en BigQuery: {errores}")
            
    except Exception as e:
        print(f"❌ Error en el proceso de almacenamiento en BigQuery: {e}")
