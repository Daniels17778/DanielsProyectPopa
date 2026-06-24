import os
import sys
import django
import logging
import tempfile
from io import BytesIO

from groq import AsyncGroq
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from decouple import config

# ====================== CONFIGURACIÓN DJANGO ======================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "popayan_all_tour.settings")
django.setup()

# ====================== CONFIGURACIÓN ======================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = config("TELEGRAM_BOT_TOKEN_TURISTAS", default="TU_TOKEN_AQUI")  # ← Cambia esto o usa variable diferente
groq_client = AsyncGroq(api_key=config("GROQ_API_KEY"))

# Diccionario para guardar el historial de cada usuario (máx 10 mensajes)
user_history: dict[int, list[dict]] = {}

# ====================== SYSTEM PROMPT (muy importante) ======================
SYSTEM_PROMPT = """
Eres el asistente oficial de **PopayanAllTour**, la plataforma turística de Popayán, Colombia.

Tu misión es ayudar a los turistas con cualquier duda sobre la aplicación web.

**Qué puedes explicar:**
- Cómo registrarse y iniciar sesión (email + contraseña o Google)
- Cómo buscar hoteles, restaurantes, museos e iglesias
- Cómo dejar reseñas y calificar establecimientos
- Cómo guardar establecimientos en favoritos
- Cómo ver noticias y eventos
- Secciones de la web: Historia de Popayán, Semana Santa, Procesiones, Juegos, Conversor de divisas, etc.
- Cómo reportar un problema o error (ej: "no me deja publicar reseña")
- Información general de Popayán y turismo

**Estilo de respuesta:**
- Siempre en español, amigable, claro y paciente.
- Usa emojis cuando ayude a entender.
- Si no sabes algo, dilo con honestidad y ofrece alternativas.
- Nunca inventes información que no exista en la app.

La app permite a los usuarios normales (turistas):
- Ver listados públicos de establecimientos
- Leer reseñas
- Guardar favoritos
- Publicar reseñas (después de registrarse)
- Leer noticias y historia

Si el usuario menciona un error técnico, ayúdalo paso a paso.
"""

# ====================== HELPERS ======================
async def get_groq_response(user_id: int, user_message: str) -> str:
    # Mantener historial (máximo 10 mensajes)
    if user_id not in user_history:
        user_history[user_id] = []

    user_history[user_id].append({"role": "user", "content": user_message})

    # Limitar historial
    if len(user_history[user_id]) > 10:
        user_history[user_id] = user_history[user_id][-10:]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + user_history[user_id]

    try:
        chat_completion = await groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",   # o "mixtral-8x7b-32768" si prefieres
            messages=messages,
            temperature=0.7,
            max_tokens=800,
        )
        response = chat_completion.choices[0].message.content.strip()

        # Guardar respuesta en historial
        user_history[user_id].append({"role": "assistant", "content": response})
        return response

    except Exception as e:
        logger.error(f"Error Groq: {e}")
        return "❌ Lo siento, tuve un problema técnico. ¿Puedes intentarlo de nuevo?"


async def transcribir_voz(update: Update) -> str | None:
    """Transcribe mensaje de voz con Groq Whisper"""
    try:
        voice = update.message.voice
        procesando = await update.message.reply_text("🎙️ Transcribiendo tu voz...")

        file = await voice.get_file()
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            tmp_path = tmp.name
        await file.download_to_drive(tmp_path)

        with open(tmp_path, "rb") as audio_file:
            transcription = await groq_client.audio.transcriptions.create(
                model="whisper-large-v3-turbo",
                file=audio_file,
                language="es",
            )
        os.unlink(tmp_path)

        await procesando.edit_text(f"✅ **Entendí:** _{transcription.text}_", parse_mode="Markdown")
        return transcription.text

    except Exception as e:
        logger.error(f"Error transcripción: {e}")
        if 'procesando' in locals():
            await procesando.edit_text("❌ No pude transcribir el audio. Intenta escribiendo.")
        return None


# ====================== HANDLERS ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌿 ¡Hola! Soy el **asistente de PopayanAllTour** 👋\n\n"
        "Estoy aquí para ayudarte con cualquier duda sobre la aplicación:\n"
        "• Cómo registrarte\n"
        "• Dejar reseñas\n"
        "• Guardar favoritos\n"
        "• Problemas técnicos\n"
        "• Información de hoteles, noticias, Semana Santa, etc.\n\n"
        "¡Pregúntame lo que quieras! 😊",
        parse_mode="Markdown",
    )


async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 **Comandos disponibles**\n\n"
        "/start — Reiniciar conversación\n"
        "/ayuda — Ver este mensaje\n"
        "/limpiar — Borrar historial de chat\n\n"
        "También puedes enviarme **mensajes de voz** 🎙️",
        parse_mode="Markdown",
    )


async def limpiar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_history.pop(user_id, None)
    await update.message.reply_text("🧹 Historial borrado. ¡Empecemos de cero!")


async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    texto = update.message.text

    if not texto:
        return

    await update.message.reply_chat_action("typing")
    respuesta = await get_groq_response(user_id, texto)
    await update.message.reply_text(respuesta, parse_mode="Markdown")


async def manejar_voz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    texto = await transcribir_voz(update)

    if not texto:
        return

    await update.message.reply_chat_action("typing")
    respuesta = await get_groq_response(user_id, texto)
    await update.message.reply_text(respuesta, parse_mode="Markdown")


# ====================== MAIN ======================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayuda", ayuda))
    app.add_handler(CommandHandler("help", ayuda))
    app.add_handler(CommandHandler("limpiar", limpiar))

    # Mensajes de texto
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))

    # Mensajes de voz
    app.add_handler(MessageHandler(filters.VOICE, manejar_voz))

    logger.info("🤖 Bot de Ayuda para Turistas de PopayanAllTour iniciado...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()