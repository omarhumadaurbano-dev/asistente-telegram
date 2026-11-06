import json
import os
import threading
import time
import urllib.request
from flask import Flask

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("8904343276:AAE0JpTYGKis2kHCAW1ZEVCRUGHwuFjxlfM")
GEMINI_API_KEY = os.environ.get("AQ.Ab8RN6I8VOb728ctW76SY8fx9XSqGK9FggEtUOk6lwOoUz1vWg")

SYSTEM_PROMPT = """
Eres un asistente personal inteligente de organización y gestión del tiempo. 
1. Analiza los fragmentos de chat o notas que te envíe el usuario.
2. Extrae puntos clave, compromisos y acuerdos importantes.
3. Organiza una lista clara de tareas pendientes para el día.
Mantén las respuestas directas, ordenadas y enfocadas en la acción.
"""


@app.route("/")
def home():
  return "¡El bot de Telegram está activo 24/7!"


def consultar_gemini(texto_usuario):
  url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
  prompt_completo = (
      f"{SYSTEM_PROMPT}\n\nMensaje o conversación:\n{texto_usuario}"
  )
  payload = {"contents": [{"parts": [{"text": prompt_completo}]}]}

  data = json.dumps(payload).encode("utf-8")
  req = urllib.request.Request(
      url, data=data, headers={"Content-Type": "application/json"}
  )

  try:
    with urllib.request.urlopen(req) as response:
      res_data = json.loads(response.read().decode("utf-8"))
      return res_data["candidates"][0]["content"]["parts"][0]["text"]
  except Exception as e:
    return f"Error con la IA: {e}"


def enviar_mensaje(chat_id, texto):
  url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
  payload = {"chat_id": chat_id, "text": texto}
  data = json.dumps(payload).encode("utf-8")
  req = urllib.request.Request(
      url, data=data, headers={"Content-Type": "application/json"}
  )
  try:
    urllib.request.urlopen(req)
  except Exception as e:
    print(f"Error al enviar mensaje: {e}")


def telegram_bot_loop():
  print("Bucle del bot iniciado...")
  offset = 0
  while True:
    try:
      url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={offset}&timeout=30"
      with urllib.request.urlopen(url) as response:
        resultado = json.loads(response.read().decode("utf-8"))

        if resultado.get("ok"):
          for update in resultado.get("result", []):
            offset = update["update_id"] + 1
            if "message" in update and "text" in update["message"]:
              chat_id = update["message"]["chat"]["id"]
              texto_usuario = update["message"]["text"]

              print(f"Mensaje recibido: {texto_usuario}")
              respuesta_ia = consultar_gemini(texto_usuario)
              enviar_mensaje(chat_id, respuesta_ia)
    except Exception as e:
      print(f"Error de red en Telegram: {e}")
      time.sleep(5)


if __name__ == "__main__":
  # Iniciar el bot de Telegram en un hilo separado
  t = threading.Thread(target=telegram_bot_loop)
  t.daemon = True
  t.start()

  # Iniciar Flask en el hilo principal (Render asigna el puerto automáticamente)
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)
