import json
import time
import random
import uuid
from google.cloud import pubsub_v1

# ================= CONFIGURACIÓN =================
PROJECT_ID = "portfolio-sentiment-ai"
TOPIC_ID = "comentarios-topic"
# =================================================

# Inicializar el cliente de Pub/Sub
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

# Catálogo de comentarios simulados para probar a Gemini
comentarios = [
    "El servicio fue excelente, la plataforma es muy intuitiva y rápida.",
    "Pésima experiencia, la aplicación se cerró sola y me cobraron dos veces. Exijo un reembolso inmediato.",
    "Está bien, cumple su función pero el diseño se ve un poco anticuado.",
    "¡Increíble! Me resolvieron mi problema de facturación en menos de 5 minutos. Muy recomendados.",
    "Llevo tres días esperando respuesta de soporte técnico por un error en mi perfil. Es una burla total.",
    "No puedo iniciar sesión desde ayer, me marca error 404 en la página principal.",
    "Los nuevos cambios en la interfaz me gustan mucho, buen trabajo al equipo de desarrollo."
]


def generar_evento():
    """Genera un payload JSON simulando un evento de sistema origen."""
    return {
        "id_mensaje": str(uuid.uuid4()),
        "texto": random.choice(comentarios),
        "origen": random.choice(["App iOS", "App Android", "Portal Web", "Twitter"])
    }


def ejecutar_simulacion(num_mensajes=5):
    print(f"🚀 Iniciando simulador. Conectando al tópico: {topic_path}\n")

    for i in range(num_mensajes):
        evento = generar_evento()
        # Pub/Sub requiere que el payload viaje como bytes
        mensaje_bytes = json.dumps(evento).encode("utf-8")

        try:
            # Publicar el mensaje
            future = publisher.publish(topic_path, data=mensaje_bytes)
            message_id = future.result()
            print(f"✅ Mensaje {message_id} publicado | Origen: {evento['origen']} | Texto: '{evento['texto'][:40]}...'")
        except Exception as e:
            print(f"❌ Error al publicar: {e}")

        # Pausa aleatoria para simular tráfico orgánico
        time.sleep(random.uniform(1.5, 4.0))

    print("\n🏁 Simulación terminada.")


if __name__ == "__main__":
    ejecutar_simulacion()

