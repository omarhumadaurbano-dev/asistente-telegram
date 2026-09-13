import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types
import edge_tts

# Cargar claves desde Render
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTION = (
    "Eres una asistente personal inteligente, atenta y eficiente. "
    "Ayudas al usuario con sus tareas escolares, organizas sus rutinas "
    "y respondes de forma clara, directa y amigable en español."
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Tu asistente ya está activa 24/7 en la nube.")

async def responder_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.chat.send_action("typing")

    try:
        response = gemini_client.models.generate_content(
            model='gemini-3.6-flash',
            contents=user_text,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"Error al responder: {e}")

async def responder_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action("record_voice")

    try:
        voice_file = await update.message.voice.get_file()
        voice_bytes = await voice_file.download_as_bytearray()

        response = gemini_client.models.generate_content(
            model='gemini-3.6-flash',
            contents=[
                types.Part.from_bytes(data=bytes(voice_bytes), mime_type='audio/ogg'),
                "Escucha este audio y responde a la duda o solicitud del usuario en español."
            ],
            config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
        )

        texto_respuesta = response.text

        tts = edge_tts.Communicate(texto_respuesta, "es-CO-SalomeNeural")
        audio_out_path = "respuesta_voz.mp3"
        await tts.save(audio_out_path)

        await update.message.reply_text(texto_respuesta)
        with open(audio_out_path, "rb") as voice_stream:
            await update.message.reply_voice(voice=voice_stream)

        if os.path.exists(audio_out_path):
            os.remove(audio_out_path)

    except Exception as e:
        await update.message.reply_text(f"Error con el audio: {e}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_texto))
    app.add_handler(MessageHandler(filters.VOICE, responder_audio))

    print("✅ Bot iniciado correctamente en Render 24/7...")
    app.run_polling()

if __name__ == "__main__":
    main()
