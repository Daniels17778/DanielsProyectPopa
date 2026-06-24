"""
Bot de Telegram para PopayanAllTour
- Login con email + contraseña
- Empresarios y Administradores: ver stats, agregar y desactivar establecimientos
- Administradores: estadísticas globales, agregar noticias

"""

import tempfile
#from openai import AsyncOpenAI

from groq import AsyncGroq
import telegram   # ← Agrega esta línea si no la tienes
import os
import sys
import django
import logging
from io import BytesIO

# ── Configurar Django ──────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "popayan_all_tour.settings")
django.setup()

from django.core.files.base import ContentFile
from django.db.models import Avg, Count
from django.utils import timezone
from asgiref.sync import sync_to_async
from popayan_all_tour1.models import (
    Usuario, Establecimiento, Resena, Favorito,
    Noticia, TipoEstablecimiento, CategoriaNoticia,
)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler,
)
from decouple import config

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = config("TELEGRAM_BOT_TOKEN", default="8274546867:AAGtHnkRbiwo33iua_bQA1EWyByd2MQ5ouM")

whisper_client = AsyncGroq(api_key=config("GROQ_API_KEY"))

#whisper_client = AsyncOpenAI(api_key=config("OPENAI_API_KEY"))

# ══════════════════════════════════════════════════════════════════════════════
# ESTADOS DE CONVERSACIÓN
# ══════════════════════════════════════════════════════════════════════════════

# Login
LOGIN_EMAIL, LOGIN_PASSWORD = range(2)

# Agregar establecimiento
(
    SITE_NOMBRE,
    SITE_DESCRIPCION,
    SITE_DIRECCION,
    SITE_HORARIO,
    SITE_TIPO,
    SITE_URL,
    SITE_IMAGEN,
    SITE_CONFIRMAR,
) = range(10, 18)

# Desactivar establecimiento
DESACT_ELEGIR, DESACT_CONFIRMAR = range(20, 22)

# Agregar noticia (solo admin)
(
    NEWS_TITULO,
    NEWS_SUBTITULO,
    NEWS_RESUMEN,
    NEWS_CONTENIDO,
    NEWS_CATEGORIA,
    NEWS_IMAGEN,
    NEWS_DESTACADA,
    NEWS_CONFIRMAR,
) = range(30, 38)

# ── Sesiones: {telegram_id: usuario_pk} ──────────────────────────────────────
sesiones: dict[int, int] = {}

# ── Datos temporales ──────────────────────────────────────────────────────────
nuevo_sitio:   dict[int, dict] = {}
nueva_noticia: dict[int, dict] = {}


# ══════════════════════════════════════════════════════════════════════════════
# HELPER: responder callback query de forma segura (evita "Query is too old")
# ══════════════════════════════════════════════════════════════════════════════

async def safe_answer(query) -> None:
    """
    Responde un callback query ignorando el error si ya expiró.
    Telegram da 10 segundos para contestar; pasado ese tiempo lanza BadRequest.
    """
    try:
        await query.answer()
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# QUERIES SÍNCRONAS
# ══════════════════════════════════════════════════════════════════════════════

def _obtener_usuario(pk: int):
    return Usuario.objects.select_related("rol", "tipo_establecimiento").get(pk=pk)

def _autenticar(email: str, password: str):
    try:
        u = Usuario.objects.select_related("rol").get(email=email, is_active=True)
    except Usuario.DoesNotExist:
        return None
    if not u.check_password(password):
        return None
    return {
        "pk": u.pk,
        "nombre_completo": u.nombre_completo,
        "is_active": u.is_active,
        "is_staff": u.is_staff,
        "rol_nombre": u.rol.rol,
    }

def _listar_tipos():
    return list(TipoEstablecimiento.objects.all().order_by("nombre"))

def _listar_categorias():
    return list(CategoriaNoticia.objects.filter(activo=True).order_by("nombre"))

def _crear_establecimiento(datos: dict, usuario_pk: int):
    tipo    = TipoEstablecimiento.objects.get(pk=datos["tipo_pk"])
    usuario = Usuario.objects.get(pk=usuario_pk)
    est = Establecimiento.objects.create(
        nombre       = datos["nombre"],
        descripcion  = datos["descripcion"],
        direccion    = datos["direccion"],
        horario_aten = datos["horario"],
        url_mas_info = datos.get("url", ""),
        tipo         = tipo,
        empresario   = usuario,
        activo       = True,
    )
    imagen_bytes = datos.get("imagen_bytes")
    imagen_nombre = datos.get("imagen_nombre", "portada.jpg")
    if imagen_bytes:
        est.imagen.save(imagen_nombre, ContentFile(imagen_bytes), save=True)
    return est

# ── Desactivar establecimiento ────────────────────────────────────────────────

def _establecimientos_activos_empresario(usuario_pk: int):
    return list(
        Establecimiento.objects
        .filter(empresario_id=usuario_pk, activo=True)
        .select_related("tipo")
        .order_by("nombre")
    )

def _todos_establecimientos_activos():
    return list(
        Establecimiento.objects
        .filter(activo=True)
        .select_related("tipo", "empresario")
        .order_by("nombre")
    )

def _desactivar_establecimiento(est_pk: int, usuario_pk: int, admin: bool) -> str:
    try:
        est = Establecimiento.objects.get(pk=est_pk) if admin else \
              Establecimiento.objects.get(pk=est_pk, empresario_id=usuario_pk)
    except Establecimiento.DoesNotExist:
        raise PermissionError("No tienes permiso para desactivar ese establecimiento.")
    est.activo = False
    est.save(update_fields=["activo"])
    return est.nombre

# ── Agregar noticia ───────────────────────────────────────────────────────────

def _crear_noticia(datos: dict, usuario_pk: int):
    usuario   = Usuario.objects.get(pk=usuario_pk)
    categoria = CategoriaNoticia.objects.get(pk=datos["categoria_pk"])
    noticia = Noticia(
        titulo            = datos["titulo"],
        subtitulo         = datos.get("subtitulo") or None,
        resumen           = datos.get("resumen") or None,
        contenido         = datos["contenido"],
        categoria         = categoria,
        autor             = usuario,
        destacada         = datos.get("destacada", False),
        publicada         = True,
        fecha_publicacion = timezone.now(),
    )
    noticia.save()
    imagen_bytes = datos.get("imagen_bytes")
    imagen_nombre = datos.get("imagen_nombre", "noticia.jpg")
    if imagen_bytes:
        noticia.imagen_principal.save(imagen_nombre, ContentFile(imagen_bytes), save=True)
    return noticia

# ── Stats empresario ──────────────────────────────────────────────────────────

def _establecimientos_empresario(usuario_pk: int):
    return list(
        Establecimiento.objects
        .filter(empresario_id=usuario_pk, activo=True)
        .select_related("tipo")
    )

def _resenas_por_establecimiento(usuario_pk: int):
    establecimientos = Establecimiento.objects.filter(empresario_id=usuario_pk)
    resultado = []
    for est in establecimientos.select_related("tipo"):
        resenas  = Resena.objects.filter(establecimiento=est)
        total    = resenas.count()
        promedio = resenas.aggregate(avg=Avg("calificacion"))["avg"]
        dist     = {i: resenas.filter(calificacion=i).count() for i in range(1, 6)}
        resultado.append({"nombre": est.nombre, "total": total, "promedio": promedio, "dist": dist})
    return resultado

def _favoritos_por_establecimiento(usuario_pk: int):
    establecimientos = Establecimiento.objects.filter(empresario_id=usuario_pk)
    return [
        {"nombre": est.nombre, "total": Favorito.objects.filter(establecimiento=est).count()}
        for est in establecimientos
    ]

def _resumen_empresario(usuario_pk: int):
    establecimientos = Establecimiento.objects.filter(empresario_id=usuario_pk)
    total_est        = establecimientos.count()
    activos          = establecimientos.filter(activo=True).count()
    total_resenas    = Resena.objects.filter(establecimiento__in=establecimientos).count()
    promedio_global  = Resena.objects.filter(
        establecimiento__in=establecimientos
    ).aggregate(avg=Avg("calificacion"))["avg"]
    total_favoritos  = Favorito.objects.filter(establecimiento__in=establecimientos).count()
    mejor = (
        establecimientos
        .annotate(avg_cal=Avg("resenas__calificacion"))
        .order_by("-avg_cal")
        .first()
    )
    return {
        "total_est": total_est, "activos": activos,
        "total_resenas": total_resenas, "promedio_global": promedio_global,
        "total_favoritos": total_favoritos,
        "mejor_nombre": mejor.nombre if mejor else None,
        "mejor_avg": getattr(mejor, "avg_cal", None) if mejor else None,
    }

# ── Stats admin ───────────────────────────────────────────────────────────────

def _stats_globales():
    return {
        "total_usuarios":         Usuario.objects.filter(is_active=True).count(),
        "total_empresarios":      Usuario.objects.filter(rol__rol__iexact="empresario", is_active=True).count(),
        "total_establecimientos": Establecimiento.objects.count(),
        "est_activos":            Establecimiento.objects.filter(activo=True).count(),
        "total_resenas":          Resena.objects.count(),
        "promedio_global":        Resena.objects.aggregate(avg=Avg("calificacion"))["avg"],
        "total_noticias":         Noticia.objects.filter(publicada=True).count(),
        "total_favoritos":        Favorito.objects.count(),
    }

def _top_establecimientos():
    return list(
        Establecimiento.objects.filter(activo=True).select_related("tipo")
        .annotate(
            avg_cal       = Avg("resenas__calificacion"),
            total_resenas = Count("resenas"),
            total_fav     = Count("favoritos"),
        ).order_by("-avg_cal", "-total_resenas")[:10]
    )

def _stats_noticias():
    total         = Noticia.objects.count()
    publicadas    = Noticia.objects.filter(publicada=True).count()
    destacadas    = Noticia.objects.filter(destacada=True, publicada=True).count()
    total_visitas = sum(Noticia.objects.values_list("visitas_totales", flat=True))
    total_fav     = Favorito.objects.filter(noticia__isnull=False).count()
    top           = list(Noticia.objects.filter(publicada=True).order_by("-visitas_totales")[:5])
    return {
        "total": total, "publicadas": publicadas, "destacadas": destacadas,
        "total_visitas": total_visitas, "total_fav": total_fav,
        "top": [(n.titulo, n.visitas_totales) for n in top],
    }

def _stats_usuarios():
    total    = Usuario.objects.filter(is_active=True).count()
    por_rol  = list(
        Usuario.objects.filter(is_active=True)
        .values("rol__rol").annotate(total=Count("id")).order_by("-total")
    )
    por_tipo = list(
        Usuario.objects.filter(is_active=True, tipo_establecimiento__isnull=False)
        .values("tipo_establecimiento__nombre").annotate(total=Count("id")).order_by("-total")
    )
    return {"total": total, "por_rol": por_rol, "por_tipo": por_tipo}


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS ASYNC
# ══════════════════════════════════════════════════════════════════════════════

async def get_usuario_async(telegram_id: int):
    pk = sesiones.get(telegram_id)
    if not pk:
        return None
    try:
        return await sync_to_async(_obtener_usuario, thread_sensitive=True)(pk)
    except Usuario.DoesNotExist:
        sesiones.pop(telegram_id, None)
        return None

def es_empresario(u) -> bool:
    return u.rol.rol.lower() == "empresario"

def es_admin(u) -> bool:
    return u.is_staff or u.rol.rol.lower() in ("administrador", "admin")

def puede_agregar_sitio(u) -> bool:
    return es_empresario(u) or es_admin(u)

def menu_principal(usuario) -> InlineKeyboardMarkup:
    botones = []
    if es_empresario(usuario):
        botones += [
            [InlineKeyboardButton("🏢 Mi Establecimiento",   callback_data="mi_establecimiento")],
            [InlineKeyboardButton("⭐ Reseñas",              callback_data="mis_resenas")],
            [InlineKeyboardButton("❤️ Favoritos",            callback_data="mis_favoritos")],
            [InlineKeyboardButton("📊 Resumen General",      callback_data="resumen_empresario")],
        ]
    if puede_agregar_sitio(usuario):
        botones += [
            [InlineKeyboardButton("➕ Agregar Sitio Turístico",    callback_data="agregar_sitio")],
            [InlineKeyboardButton("🗑️ Desactivar Sitio Turístico", callback_data="desactivar_sitio")],
        ]
    if es_admin(usuario):
        botones += [
            [InlineKeyboardButton("📰 Publicar Noticia",         callback_data="agregar_noticia")],
            [InlineKeyboardButton("📈 Estadísticas Globales",    callback_data="stats_globales")],
            [InlineKeyboardButton("🏆 Top Establecimientos",     callback_data="top_establecimientos")],
            [InlineKeyboardButton("📊 Estadísticas Noticias",    callback_data="stats_noticias")],
            [InlineKeyboardButton("👥 Usuarios Registrados",     callback_data="stats_usuarios")],
        ]
    botones.append([InlineKeyboardButton("🚪 Cerrar Sesión", callback_data="logout")])
    return InlineKeyboardMarkup(botones)

BOTON_VOLVER = InlineKeyboardMarkup([[
    InlineKeyboardButton("🔙 Volver al Menú", callback_data="volver_menu")
]])

def cancelar_teclado():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_flujo")]])

def omitir_cancelar_teclado(omitir_data: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭️ Omitir",   callback_data=omitir_data)],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_flujo")],
    ])


# ══════════════════════════════════════════════════════════════════════════════
# LOGIN
# ══════════════════════════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario = await get_usuario_async(update.effective_user.id)
    if usuario:
        await update.message.reply_text(
            f"👋 ¡Hola de nuevo, *{usuario.nombre_completo}*!\n\nUsa el menú para navegar:",
            parse_mode="Markdown", reply_markup=menu_principal(usuario),
        )
    else:
        await update.message.reply_text(
            "🌿 *Bienvenido al Bot de PopayanAllTour*\n\n"
            "Disponible para *empresarios* y *administradores*.\n\n"
            "Usa /login para iniciar sesión.",
            parse_mode="Markdown",
        )

async def login_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario = await get_usuario_async(update.effective_user.id)
    if usuario:
        await update.message.reply_text(
            f"✅ Ya estás autenticado como *{usuario.nombre_completo}*.",
            parse_mode="Markdown", reply_markup=menu_principal(usuario),
        )
        return ConversationHandler.END
    await update.message.reply_text(
        "🔐 *Inicio de sesión*\n\n📧 Escribe tu correo electrónico:",
        parse_mode="Markdown",
    )
    return LOGIN_EMAIL

async def login_recibir_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["login_email"] = update.message.text.strip().lower()
    await update.message.reply_text(
        "🔑 Ahora escribe tu *contraseña*:\n\n_(tu mensaje será borrado inmediatamente)_",
        parse_mode="Markdown",
    )
    return LOGIN_PASSWORD

async def login_recibir_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password    = update.message.text.strip()
    email       = context.user_data.get("login_email", "")
    telegram_id = update.effective_user.id
    try:
        await update.message.delete()
    except Exception:
        pass
    datos = await sync_to_async(_autenticar, thread_sensitive=True)(email, password)
    if not datos:
        await update.effective_chat.send_message(
            "❌ *Correo o contraseña incorrectos.*\n\nIntenta de nuevo con /login",
            parse_mode="Markdown",
        )
        return ConversationHandler.END
    rol = datos["rol_nombre"].lower()
    if rol not in ("empresario", "administrador", "admin") and not datos["is_staff"]:
        await update.effective_chat.send_message(
            "⛔ Este bot está disponible únicamente para *empresarios* y *administradores*.",
            parse_mode="Markdown",
        )
        return ConversationHandler.END
    sesiones[telegram_id] = datos["pk"]
    context.user_data.clear()
    usuario = await get_usuario_async(telegram_id)
    await update.effective_chat.send_message(
        f"✅ ¡Bienvenido, *{datos['nombre_completo']}*!\n"
        f"🎭 Rol: *{datos['rol_nombre']}*\n\nSelecciona una opción:",
        parse_mode="Markdown", reply_markup=menu_principal(usuario),
    )
    return ConversationHandler.END

async def login_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Login cancelado. Usa /login cuando quieras.")
    return ConversationHandler.END


# ══════════════════════════════════════════════════════════════════════════════
# CANCELAR FLUJO GENÉRICO
# ══════════════════════════════════════════════════════════════════════════════

async def cancelar_flujo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tid = update.effective_user.id
    nuevo_sitio.pop(tid, None)
    nueva_noticia.pop(tid, None)
    context.user_data.clear()
    if update.callback_query:
        await safe_answer(update.callback_query)
        await update.callback_query.message.reply_text(
            "❌ Operación cancelada.", reply_markup=BOTON_VOLVER,
        )
    else:
        await update.message.reply_text("❌ Operación cancelada.", reply_markup=BOTON_VOLVER)
    return ConversationHandler.END


# ══════════════════════════════════════════════════════════════════════════════
# AGREGAR SITIO TURÍSTICO
# ══════════════════════════════════════════════════════════════════════════════

async def sitio_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await safe_answer(update.callback_query)
        send = update.callback_query.message.reply_text
    else:
        send = update.message.reply_text
    usuario = await get_usuario_async(update.effective_user.id)
    if not usuario or not puede_agregar_sitio(usuario):
        await send("⛔ Solo empresarios y administradores pueden agregar sitios turísticos.")
        return ConversationHandler.END
    nuevo_sitio[update.effective_user.id] = {}
    await send(
        "🏗️ *Nuevo Sitio Turístico*\n\n"
        "Puedes cancelar en cualquier momento con /cancelar\n\n"
        "📝 *Paso 1/7* — ¿Cuál es el *nombre* del sitio?",
        parse_mode="Markdown", reply_markup=cancelar_teclado(),
    )
    return SITE_NOMBRE

async def sitio_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nuevo_sitio[update.effective_user.id]["nombre"] = update.message.text.strip()
    await update.message.reply_text(
        "📝 *Paso 2/7* — Escribe una *descripción* del sitio:",
        parse_mode="Markdown", reply_markup=cancelar_teclado(),
    )
    return SITE_DESCRIPCION

async def sitio_descripcion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nuevo_sitio[update.effective_user.id]["descripcion"] = update.message.text.strip()
    await update.message.reply_text(
        "📝 *Paso 3/7* — ¿Cuál es la *dirección*?",
        parse_mode="Markdown", reply_markup=cancelar_teclado(),
    )
    return SITE_DIRECCION

async def sitio_direccion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nuevo_sitio[update.effective_user.id]["direccion"] = update.message.text.strip()
    await update.message.reply_text(
        "📝 *Paso 4/7* — ¿Cuál es el *horario de atención*?\n"
        "_(Ej: Lun-Vie 8am-6pm, Sáb 9am-3pm)_",
        parse_mode="Markdown", reply_markup=cancelar_teclado(),
    )
    return SITE_HORARIO

async def sitio_horario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nuevo_sitio[update.effective_user.id]["horario"] = update.message.text.strip()
    tipos = await sync_to_async(_listar_tipos, thread_sensitive=True)()
    if not tipos:
        await update.message.reply_text(
            "⚠️ No hay tipos de establecimiento registrados. Pídele al administrador que los cree."
        )
        nuevo_sitio.pop(update.effective_user.id, None)
        return ConversationHandler.END
    context.user_data["tipos"] = {str(t.pk): t.nombre for t in tipos}
    botones = [[InlineKeyboardButton(t.nombre, callback_data=f"tipo_{t.pk}")] for t in tipos]
    botones.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_flujo")])
    await update.message.reply_text(
        "📝 *Paso 5/7* — Selecciona el *tipo de establecimiento*:",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(botones),
    )
    return SITE_TIPO

async def sitio_tipo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await safe_answer(query)
    tipo_pk    = int(query.data.replace("tipo_", ""))
    tipo_nombre = context.user_data.get("tipos", {}).get(str(tipo_pk), "Desconocido")
    nuevo_sitio[update.effective_user.id]["tipo_pk"]     = tipo_pk
    nuevo_sitio[update.effective_user.id]["tipo_nombre"] = tipo_nombre
    await query.message.reply_text(
        "📝 *Paso 6/7* — ¿Tienes una *URL* con más información?\n"
        "_(Ej: https://misitioweb.com — escribe `ninguna` si no tienes)_",
        parse_mode="Markdown", reply_markup=cancelar_teclado(),
    )
    return SITE_URL

async def sitio_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    url   = "" if texto.lower() in ("ninguna", "no", "n/a", "-") else texto
    nuevo_sitio[update.effective_user.id]["url"] = url
    await update.message.reply_text(
        "🖼️ *Paso 7/7* — Envía una *foto de portada* para el sitio.\n"
        "_(Envía la imagen como foto de Telegram)_",
        parse_mode="Markdown", reply_markup=omitir_cancelar_teclado("omitir_imagen_sitio"),
    )
    return SITE_IMAGEN

async def sitio_imagen_recibida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tid   = update.effective_user.id
    photo = update.message.photo[-1]
    buf   = BytesIO()
    await (await photo.get_file()).download_to_memory(buf)
    nuevo_sitio[tid]["imagen_bytes"]  = buf.getvalue()
    nuevo_sitio[tid]["imagen_nombre"] = f"sitio_{tid}_{photo.file_unique_id}.jpg"
    await _mostrar_resumen_sitio(update.message.reply_text, tid)
    return SITE_CONFIRMAR

async def sitio_imagen_omitida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_answer(update.callback_query)
    tid = update.effective_user.id
    nuevo_sitio[tid]["imagen_bytes"]  = None
    nuevo_sitio[tid]["imagen_nombre"] = None
    await _mostrar_resumen_sitio(update.callback_query.message.reply_text, tid)
    return SITE_CONFIRMAR

async def _mostrar_resumen_sitio(send_fn, tid: int):
    d = nuevo_sitio[tid]
    await send_fn(
        f"✅ *Resumen del nuevo sitio:*\n\n"
        f"🏷️ Nombre: *{d['nombre']}*\n"
        f"📋 Descripción: {d['descripcion']}\n"
        f"📍 Dirección: {d['direccion']}\n"
        f"🕐 Horario: {d['horario']}\n"
        f"🏢 Tipo: {d['tipo_nombre']}\n"
        f"🔗 URL: {d['url'] or '_(sin URL)_'}\n"
        f"🖼️ Imagen: {'✅ Adjunta' if d.get('imagen_bytes') else '_(sin imagen)_'}\n\n"
        f"¿Confirmas la creación?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Confirmar", callback_data="confirmar_sitio"),
            InlineKeyboardButton("❌ Cancelar",  callback_data="cancelar_flujo"),
        ]]),
    )

async def sitio_confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    await safe_answer(query)
    tid     = update.effective_user.id
    datos   = nuevo_sitio.get(tid)
    if not datos:
        await query.message.reply_text("⚠️ No hay datos. Usa /agregar para empezar.")
        return ConversationHandler.END
    usuario = await get_usuario_async(tid)
    try:
        est = await sync_to_async(_crear_establecimiento, thread_sensitive=True)(datos, usuario.pk)
        nuevo_sitio.pop(tid, None)
        context.user_data.clear()
        await query.message.reply_text(
            f"🎉 *¡Sitio creado exitosamente!*\n\n"
            f"🏷️ *{est.nombre}* ya está registrado en PopayanAllTour.",
            parse_mode="Markdown", reply_markup=menu_principal(usuario),
        )
    except Exception as e:
        logger.error(f"Error creando establecimiento: {e}")
        await query.message.reply_text(
            f"❌ Error al guardar: `{e}`\n\nIntenta de nuevo con /agregar",
            parse_mode="Markdown",
        )
    return ConversationHandler.END


# ══════════════════════════════════════════════════════════════════════════════
# DESACTIVAR SITIO TURÍSTICO
# ══════════════════════════════════════════════════════════════════════════════

async def desactivar_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await safe_answer(update.callback_query)
        send = update.callback_query.message.reply_text
    else:
        send = update.message.reply_text

    usuario = await get_usuario_async(update.effective_user.id)
    if not usuario or not puede_agregar_sitio(usuario):
        await send("⛔ No tienes permiso para desactivar sitios.")
        return ConversationHandler.END

    # Admin ve todos; empresario solo los suyos
    if es_admin(usuario):
        establecimientos = await sync_to_async(_todos_establecimientos_activos, thread_sensitive=True)()
    else:
        establecimientos = await sync_to_async(
            _establecimientos_activos_empresario, thread_sensitive=True
        )(usuario.pk)

    if not establecimientos:
        await send("📭 No hay establecimientos activos para desactivar.")
        return ConversationHandler.END

    context.user_data["desact_mapa"] = {str(e.pk): e.nombre for e in establecimientos}

    botones = []
    for est in establecimientos:
        etiqueta = est.nombre
        # El admin ve también el nombre del empresario para distinguir
        if es_admin(usuario) and est.empresario:
            etiqueta += f" ({est.empresario.nombre_completo})"
        botones.append([InlineKeyboardButton(etiqueta, callback_data=f"desact_{est.pk}")])
    botones.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_flujo")])

    await send(
        "🗑️ *Desactivar Sitio Turístico*\n\n"
        "Selecciona el sitio que deseas desactivar:\n"
        "_(El sitio quedará oculto pero no se borrará de la base de datos)_",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(botones),
    )
    return DESACT_ELEGIR

async def desactivar_elegido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await safe_answer(query)
    est_pk = int(query.data.replace("desact_", ""))
    nombre = context.user_data.get("desact_mapa", {}).get(str(est_pk), "ese sitio")
    context.user_data["desact_pk"]     = est_pk
    context.user_data["desact_nombre"] = nombre

    await query.message.reply_text(
        f"⚠️ *¿Estás seguro?*\n\n"
        f"Vas a desactivar: *{nombre}*\n\n"
        f"El sitio quedará *invisible* para los turistas pero todos sus datos se conservarán.\n"
        f"Podrás reactivarlo desde el panel de administración web.\n\n"
        f"¿Confirmas la desactivación?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Sí, desactivar", callback_data="confirmar_desact"),
            InlineKeyboardButton("❌ No, cancelar",   callback_data="cancelar_flujo"),
        ]]),
    )
    return DESACT_CONFIRMAR

async def desactivar_confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    await safe_answer(query)
    tid     = update.effective_user.id
    usuario = await get_usuario_async(tid)
    est_pk  = context.user_data.get("desact_pk")

    try:
        nombre_real = await sync_to_async(
            _desactivar_establecimiento, thread_sensitive=True
        )(est_pk, usuario.pk, es_admin(usuario))
        context.user_data.clear()
        await query.message.reply_text(
            f"✅ *¡Sitio desactivado correctamente!*\n\n"
            f"🏷️ *{nombre_real}* ya no es visible para los turistas.\n"
            f"Puedes reactivarlo desde el panel de administración web.",
            parse_mode="Markdown", reply_markup=menu_principal(usuario),
        )
    except PermissionError as e:
        await query.message.reply_text(f"⛔ {e}", reply_markup=BOTON_VOLVER)
    except Exception as e:
        logger.error(f"Error desactivando establecimiento: {e}")
        await query.message.reply_text(
            f"❌ Error al desactivar: `{e}`", parse_mode="Markdown", reply_markup=BOTON_VOLVER,
        )
    return ConversationHandler.END


# ══════════════════════════════════════════════════════════════════════════════
# AGREGAR NOTICIA (solo administradores)
# ══════════════════════════════════════════════════════════════════════════════

async def noticia_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await safe_answer(update.callback_query)
        send = update.callback_query.message.reply_text
    else:
        send = update.message.reply_text
    usuario = await get_usuario_async(update.effective_user.id)
    if not usuario or not es_admin(usuario):
        await send("⛔ Solo los administradores pueden publicar noticias.")
        return ConversationHandler.END
    nueva_noticia[update.effective_user.id] = {}
    await send(
        "📰 *Nueva Noticia*\n\n"
        "Puedes cancelar en cualquier momento con /cancelar\n\n"
        "📝 *Paso 1/7* — Escribe el *título* de la noticia:",
        parse_mode="Markdown", reply_markup=cancelar_teclado(),
    )
    return NEWS_TITULO

async def noticia_titulo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nueva_noticia[update.effective_user.id]["titulo"] = update.message.text.strip()
    await update.message.reply_text(
        "📝 *Paso 2/7* — Escribe el *subtítulo* _(opcional)_:",
        parse_mode="Markdown", reply_markup=omitir_cancelar_teclado("omitir_subtitulo"),
    )
    return NEWS_SUBTITULO

async def noticia_subtitulo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nueva_noticia[update.effective_user.id]["subtitulo"] = update.message.text.strip()
    await update.message.reply_text(
        "📝 *Paso 3/7* — Escribe el *resumen* _(máx. 500 caracteres, opcional)_:",
        parse_mode="Markdown", reply_markup=omitir_cancelar_teclado("omitir_resumen"),
    )
    return NEWS_RESUMEN

async def noticia_subtitulo_omitido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_answer(update.callback_query)
    nueva_noticia[update.effective_user.id]["subtitulo"] = ""
    await update.callback_query.message.reply_text(
        "📝 *Paso 3/7* — Escribe el *resumen* _(máx. 500 caracteres, opcional)_:",
        parse_mode="Markdown", reply_markup=omitir_cancelar_teclado("omitir_resumen"),
    )
    return NEWS_RESUMEN

async def noticia_resumen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nueva_noticia[update.effective_user.id]["resumen"] = update.message.text.strip()[:500]
    await update.message.reply_text(
        "📝 *Paso 4/7* — Escribe el *contenido completo* de la noticia:",
        parse_mode="Markdown", reply_markup=cancelar_teclado(),
    )
    return NEWS_CONTENIDO

async def noticia_resumen_omitido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_answer(update.callback_query)
    nueva_noticia[update.effective_user.id]["resumen"] = ""
    await update.callback_query.message.reply_text(
        "📝 *Paso 4/7* — Escribe el *contenido completo* de la noticia:",
        parse_mode="Markdown", reply_markup=cancelar_teclado(),
    )
    return NEWS_CONTENIDO

async def noticia_contenido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nueva_noticia[update.effective_user.id]["contenido"] = update.message.text.strip()
    categorias = await sync_to_async(_listar_categorias, thread_sensitive=True)()
    if not categorias:
        await update.message.reply_text(
            "⚠️ No hay categorías de noticias activas. Créalas primero en el panel web."
        )
        nueva_noticia.pop(update.effective_user.id, None)
        return ConversationHandler.END
    context.user_data["cats"] = {str(c.pk): c.nombre for c in categorias}
    botones = [[InlineKeyboardButton(c.nombre, callback_data=f"cat_{c.pk}")] for c in categorias]
    botones.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_flujo")])
    await update.message.reply_text(
        "📝 *Paso 5/7* — Selecciona la *categoría* de la noticia:",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(botones),
    )
    return NEWS_CATEGORIA

async def noticia_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await safe_answer(query)
    cat_pk     = int(query.data.replace("cat_", ""))
    cat_nombre = context.user_data.get("cats", {}).get(str(cat_pk), "Desconocida")
    nueva_noticia[update.effective_user.id]["categoria_pk"]    = cat_pk
    nueva_noticia[update.effective_user.id]["categoria_nombre"] = cat_nombre
    await query.message.reply_text(
        "🖼️ *Paso 6/7* — Envía la *imagen principal* de la noticia.\n"
        "_(Envía la imagen como foto de Telegram)_",
        parse_mode="Markdown", reply_markup=omitir_cancelar_teclado("omitir_imagen_noticia"),
    )
    return NEWS_IMAGEN

async def noticia_imagen_recibida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tid   = update.effective_user.id
    photo = update.message.photo[-1]
    buf   = BytesIO()
    await (await photo.get_file()).download_to_memory(buf)
    nueva_noticia[tid]["imagen_bytes"]  = buf.getvalue()
    nueva_noticia[tid]["imagen_nombre"] = f"noticia_{tid}_{photo.file_unique_id}.jpg"
    await _preguntar_destacada(update.message.reply_text)
    return NEWS_DESTACADA

async def noticia_imagen_omitida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_answer(update.callback_query)
    tid = update.effective_user.id
    nueva_noticia[tid]["imagen_bytes"]  = None
    nueva_noticia[tid]["imagen_nombre"] = None
    await _preguntar_destacada(update.callback_query.message.reply_text)
    return NEWS_DESTACADA

async def _preguntar_destacada(send_fn):
    await send_fn(
        "⭐ *Paso 7/7* — ¿Quieres marcar esta noticia como *destacada*?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("⭐ Sí, destacar", callback_data="noticia_destacada_si"),
                InlineKeyboardButton("➡️ No destacar",  callback_data="noticia_destacada_no"),
            ],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_flujo")],
        ]),
    )

async def noticia_destacada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await safe_answer(query)
    tid   = update.effective_user.id
    nueva_noticia[tid]["destacada"] = (query.data == "noticia_destacada_si")
    await _mostrar_resumen_noticia(query.message.reply_text, tid)
    return NEWS_CONFIRMAR

async def _mostrar_resumen_noticia(send_fn, tid: int):
    d       = nueva_noticia[tid]
    resumen = d.get("resumen") or "_(sin resumen)_"
    resumen_preview = resumen[:80] + ("..." if len(resumen) > 80 else "")
    await send_fn(
        f"✅ *Resumen de la nueva noticia:*\n\n"
        f"📰 Título: *{d['titulo']}*\n"
        f"💬 Subtítulo: {d.get('subtitulo') or '_(sin subtítulo)_'}\n"
        f"📋 Resumen: {resumen_preview}\n"
        f"📄 Contenido: {d['contenido'][:60]}...\n"
        f"🗂️ Categoría: {d['categoria_nombre']}\n"
        f"🖼️ Imagen: {'✅ Adjunta' if d.get('imagen_bytes') else '_(sin imagen)_'}\n"
        f"⭐ Destacada: {'Sí ⭐' if d.get('destacada') else 'No'}\n\n"
        f"¿Confirmas la publicación?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Publicar",  callback_data="confirmar_noticia"),
            InlineKeyboardButton("❌ Cancelar",  callback_data="cancelar_flujo"),
        ]]),
    )

async def noticia_confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    await safe_answer(query)
    tid     = update.effective_user.id
    datos   = nueva_noticia.get(tid)
    if not datos:
        await query.message.reply_text("⚠️ No hay datos. Usa /noticia para empezar.")
        return ConversationHandler.END
    usuario = await get_usuario_async(tid)
    try:
        noticia = await sync_to_async(_crear_noticia, thread_sensitive=True)(datos, usuario.pk)
        nueva_noticia.pop(tid, None)
        context.user_data.clear()
        await query.message.reply_text(
            f"🎉 *¡Noticia publicada exitosamente!*\n\n"
            f"📰 *{noticia.titulo}* ya está disponible en PopayanAllTour.",
            parse_mode="Markdown", reply_markup=menu_principal(usuario),
        )
    except Exception as e:
        logger.error(f"Error creando noticia: {e}")
        await query.message.reply_text(
            f"❌ Error al publicar: `{e}`\n\nIntenta de nuevo con /noticia",
            parse_mode="Markdown",
        )
    return ConversationHandler.END


# ══════════════════════════════════════════════════════════════════════════════
# COMANDOS SIMPLES
# ══════════════════════════════════════════════════════════════════════════════

async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario = await get_usuario_async(update.effective_user.id)
    if not usuario:
        await update.message.reply_text("⚠️ Debes iniciar sesión primero con /login")
        return
    await update.message.reply_text(
        "📋 *Menú Principal*", parse_mode="Markdown", reply_markup=menu_principal(usuario),
    )

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *Comandos disponibles:*\n\n"
        "/start — Bienvenida\n"
        "/login — Iniciar sesión\n"
        "/menu — Menú principal\n"
        "/agregar — Agregar sitio turístico _(empresarios y admins)_\n"
        "/desactivar — Desactivar sitio turístico _(empresarios y admins)_\n"
        "/noticia — Publicar noticia _(solo admins)_\n"
        "/logout — Cerrar sesión\n"
        "/cancelar — Cancelar operación en curso\n"
        "/ayuda — Esta ayuda\n",
        parse_mode="Markdown",
    )

async def logout_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tid = update.effective_user.id
    sesiones.pop(tid, None)
    nuevo_sitio.pop(tid, None)
    nueva_noticia.pop(tid, None)
    context.user_data.clear()
    await update.message.reply_text("👋 Sesión cerrada. ¡Hasta pronto!")


# ══════════════════════════════════════════════════════════════════════════════
# CALLBACKS DE BOTONES (stats y navegación)
# ══════════════════════════════════════════════════════════════════════════════

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    # Responder inmediatamente para evitar "Query is too old"
    await safe_answer(query)
    tid     = update.effective_user.id
    usuario = await get_usuario_async(tid)

    if not usuario:
        await query.edit_message_text("⚠️ Sesión expirada. Usa /login")
        return

    data = query.data

    if data == "logout":
        sesiones.pop(tid, None)
        await query.edit_message_text("👋 Sesión cerrada. Usa /login para volver.")
        return

    if data == "volver_menu":
        await query.edit_message_text(
            "📋 *Menú Principal*", parse_mode="Markdown", reply_markup=menu_principal(usuario),
        )
        return

    # Redirigir a los flujos (los ConversationHandlers los manejan por comando)
    if data in ("agregar_sitio", "desactivar_sitio", "agregar_noticia"):
        comandos = {
            "agregar_sitio":    "/agregar",
            "desactivar_sitio": "/desactivar",
            "agregar_noticia":  "/noticia",
        }
        await query.message.reply_text(
            f"Escribe {comandos[data]} para iniciar el proceso."
        )
        return

    # ── EMPRESARIO ─────────────────────────────────────────────────────────────

    if data == "mi_establecimiento":
        if not es_empresario(usuario):
            await query.edit_message_text("⛔ Solo disponible para empresarios.", reply_markup=BOTON_VOLVER)
            return
        ests = await sync_to_async(_establecimientos_empresario, thread_sensitive=True)(usuario.pk)
        if not ests:
            await query.edit_message_text("📭 No tienes establecimientos activos.", reply_markup=BOTON_VOLVER)
            return
        texto = "🏢 *Tus Establecimientos Activos:*\n\n"
        for est in ests:
            texto += (
                f"📍 *{est.nombre}*\n"
                f"   Tipo: {est.tipo.nombre}\n"
                f"   Dirección: {est.direccion}\n"
                f"   Horario: {est.horario_aten}\n\n"
            )
        await query.edit_message_text(texto, parse_mode="Markdown", reply_markup=BOTON_VOLVER)

    elif data == "mis_resenas":
        if not es_empresario(usuario):
            await query.edit_message_text("⛔ Solo disponible para empresarios.", reply_markup=BOTON_VOLVER)
            return
        datos = await sync_to_async(_resenas_por_establecimiento, thread_sensitive=True)(usuario.pk)
        if not datos:
            await query.edit_message_text("📭 No tienes establecimientos.", reply_markup=BOTON_VOLVER)
            return
        texto = "⭐ *Reseñas de tus Establecimientos:*\n\n"
        for d in datos:
            promedio_str = f"{d['promedio']:.1f}" if d['promedio'] else "Sin calificaciones"
            dist_str     = " | ".join([f"{i}★:{d['dist'][i]}" for i in range(5, 0, -1)])
            texto += (
                f"🏢 *{d['nombre']}*\n"
                f"   Total: {d['total']}  |  Promedio: {promedio_str} ⭐\n"
                f"   Distribución: {dist_str}\n\n"
            )
        await query.edit_message_text(texto, parse_mode="Markdown", reply_markup=BOTON_VOLVER)

    elif data == "mis_favoritos":
        if not es_empresario(usuario):
            await query.edit_message_text("⛔ Solo disponible para empresarios.", reply_markup=BOTON_VOLVER)
            return
        datos = await sync_to_async(_favoritos_por_establecimiento, thread_sensitive=True)(usuario.pk)
        texto  = "❤️ *Favoritos de tus Establecimientos:*\n\n"
        for d in datos:
            texto += f"🏢 *{d['nombre']}*: {d['total']} personas lo han guardado ❤️\n"
        if not datos:
            texto += "No tienes establecimientos registrados."
        await query.edit_message_text(texto, parse_mode="Markdown", reply_markup=BOTON_VOLVER)

    elif data == "resumen_empresario":
        if not es_empresario(usuario):
            await query.edit_message_text("⛔ Solo disponible para empresarios.", reply_markup=BOTON_VOLVER)
            return
        d            = await sync_to_async(_resumen_empresario, thread_sensitive=True)(usuario.pk)
        promedio_str = f"{d['promedio_global']:.1f}" if d['promedio_global'] else "N/A"
        mejor_str    = f"{d['mejor_nombre']} ({d['mejor_avg']:.1f}⭐)" if d['mejor_nombre'] and d['mejor_avg'] else "N/A"
        texto = (
            f"📊 *Resumen de tu Negocio*\n\n"
            f"🏢 Establecimientos: {d['total_est']} ({d['activos']} activos)\n"
            f"⭐ Total reseñas: {d['total_resenas']}\n"
            f"📈 Calificación promedio: {promedio_str} ⭐\n"
            f"❤️ Guardado en favoritos: {d['total_favoritos']}\n"
            f"🏆 Mejor calificado: {mejor_str}\n"
        )
        await query.edit_message_text(texto, parse_mode="Markdown", reply_markup=BOTON_VOLVER)

    # ── ADMINISTRADOR ──────────────────────────────────────────────────────────

    elif data == "stats_globales":
        if not es_admin(usuario):
            await query.edit_message_text("⛔ Solo disponible para administradores.", reply_markup=BOTON_VOLVER)
            return
        d            = await sync_to_async(_stats_globales, thread_sensitive=True)()
        promedio_str = f"{d['promedio_global']:.2f}" if d['promedio_global'] else "N/A"
        texto = (
            f"📈 *Estadísticas Globales de PopayanAllTour*\n\n"
            f"👥 Usuarios activos: {d['total_usuarios']}\n"
            f"🧑‍💼 Empresarios: {d['total_empresarios']}\n"
            f"🏢 Establecimientos: {d['total_establecimientos']} ({d['est_activos']} activos)\n"
            f"⭐ Reseñas totales: {d['total_resenas']}\n"
            f"📊 Calificación promedio global: {promedio_str} ⭐\n"
            f"📰 Noticias publicadas: {d['total_noticias']}\n"
            f"❤️ Favoritos guardados: {d['total_favoritos']}\n"
        )
        await query.edit_message_text(texto, parse_mode="Markdown", reply_markup=BOTON_VOLVER)

    elif data == "top_establecimientos":
        if not es_admin(usuario):
            await query.edit_message_text("⛔ Solo disponible para administradores.", reply_markup=BOTON_VOLVER)
            return
        top = await sync_to_async(_top_establecimientos, thread_sensitive=True)()
        if not top:
            await query.edit_message_text("📭 No hay establecimientos con datos aún.", reply_markup=BOTON_VOLVER)
            return
        texto = "🏆 *Top 10 Establecimientos*\n\n"
        for i, est in enumerate(top, 1):
            avg    = f"{est.avg_cal:.1f}" if est.avg_cal else "Sin reseñas"
            texto += (
                f"{i}. *{est.nombre}*\n"
                f"   Tipo: {est.tipo.nombre}\n"
                f"   {avg} ⭐ | {est.total_resenas} reseñas | ❤️ {est.total_fav}\n\n"
            )
        await query.edit_message_text(texto, parse_mode="Markdown", reply_markup=BOTON_VOLVER)

    elif data == "stats_noticias":
        if not es_admin(usuario):
            await query.edit_message_text("⛔ Solo disponible para administradores.", reply_markup=BOTON_VOLVER)
            return
        d     = await sync_to_async(_stats_noticias, thread_sensitive=True)()
        texto = (
            f"📰 *Estadísticas de Noticias*\n\n"
            f"📄 Total noticias: {d['total']}\n"
            f"✅ Publicadas: {d['publicadas']}\n"
            f"🌟 Destacadas: {d['destacadas']}\n"
            f"👁️ Visitas totales: {d['total_visitas']:,}\n"
            f"❤️ Guardadas en favoritos: {d['total_fav']}\n\n"
            f"*📊 Top 5 más visitadas:*\n"
        )
        for i, (titulo, visitas) in enumerate(d['top'], 1):
            texto += f"{i}. {titulo[:40]} — {visitas:,} visitas\n"
        await query.edit_message_text(texto, parse_mode="Markdown", reply_markup=BOTON_VOLVER)

    elif data == "stats_usuarios":
        if not es_admin(usuario):
            await query.edit_message_text("⛔ Solo disponible para administradores.", reply_markup=BOTON_VOLVER)
            return
        d     = await sync_to_async(_stats_usuarios, thread_sensitive=True)()
        texto = (
            f"👥 *Estadísticas de Usuarios*\n\n"
            f"Total activos: {d['total']}\n\n"
            f"*Por Rol:*\n"
        )
        for r in d['por_rol']:
            texto += f"  • {r['rol__rol']}: {r['total']}\n"
        if d['por_tipo']:
            texto += "\n*Empresarios por Tipo de Negocio:*\n"
            for t in d['por_tipo']:
                texto += f"  • {t['tipo_establecimiento__nombre']}: {t['total']}\n"
        await query.edit_message_text(texto, parse_mode="Markdown", reply_markup=BOTON_VOLVER)

    else:
        await query.edit_message_text("❓ Opción no reconocida.", reply_markup=BOTON_VOLVER)


# ══════════════════════════════════════════════════════════════════════════════
# COMANDOS DE VOZ (audio → texto → acción)
# ══════════════════════════════════════════════════════════════════════════════

# Mapa de intenciones: palabras clave → callback_data o comando interno
INTENCIONES = [
    # Stats globales
    (["estadísticas globales", "stats globales", "estadisticas globales",
      "estadísticas generales", "resumen global", "datos globales"], "stats_globales"),
    # Top establecimientos
    (["top establecimiento", "mejores establecimiento", "ranking establecimiento",
      "top sitio", "mejores sitios"], "top_establecimientos"),
    # Stats noticias
    (["estadísticas noticias", "stats noticias", "estadisticas noticias",
      "datos noticias"], "stats_noticias"),
    # Stats usuarios
    (["estadísticas usuarios", "stats usuarios", "usuarios registrados",
      "cuántos usuarios", "cuantos usuarios"], "stats_usuarios"),
    # Mi establecimiento
    (["mi establecimiento", "mis establecimientos", "ver establecimiento"], "mi_establecimiento"),
    # Reseñas
    (["mis reseñas", "mis resenas", "ver reseñas", "ver resenas",
      "reseñas de mis", "calificaciones"], "mis_resenas"),
    # Favoritos
    (["mis favoritos", "ver favoritos", "guardados"], "mis_favoritos"),
    # Resumen empresario
    (["resumen negocio", "resumen empresario", "resumen general",
      "estadísticas negocio", "mi resumen"], "resumen_empresario"),
    # Agregar sitio
    (["agregar sitio", "añadir sitio", "nuevo sitio", "crear sitio",
      "agregar establecimiento", "nuevo establecimiento"], "agregar_sitio"),
    # Desactivar sitio
    (["desactivar sitio", "desactivar establecimiento", "eliminar sitio",
      "ocultar sitio", "borrar sitio"], "desactivar_sitio"),
    # Agregar noticia
    (["agregar noticia", "nueva noticia", "publicar noticia",
      "crear noticia", "añadir noticia"], "agregar_noticia"),
    # Logout
    (["cerrar sesión", "cerrar sesion", "salir", "logout", "desconectar"], "logout"),
    # Menú
    (["menú", "menu", "ir al menú", "ir al menu", "opciones", "mostrar menú"], "volver_menu"),
]

def _detectar_intencion(texto: str) -> str | None:
    """Mapea texto transcripto a un callback_data conocido."""
    texto_lower = texto.lower().strip()
    # Eliminar signos de puntuación comunes
    for char in [".", ",", "¿", "?", "¡", "!"]:
        texto_lower = texto_lower.replace(char, "")

    mejor_match = None
    mejor_longitud = 0  # preferimos el match más específico (más largo)

    for palabras_clave, accion in INTENCIONES:
        for frase in palabras_clave:
            if frase in texto_lower and len(frase) > mejor_longitud:
                mejor_match = accion
                mejor_longitud = len(frase)

    return mejor_match


async def _transcribir_audio(file_path: str) -> str:
    with open(file_path, "rb") as audio_file:
        response = await whisper_client.audio.transcriptions.create(
            model="whisper-large-v3-turbo",  # modelo de Groq
            file=audio_file,
            language="es",
        )
    return response.text


async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja mensajes de voz - Prioriza flujos activos"""
    tid = update.effective_user.id
    usuario = await get_usuario_async(tid)
    if not usuario:
        await update.message.reply_text("⚠️ Debes iniciar sesión primero con /login.")
        return

    # === PRIORIDAD 1: Si estamos dentro de un flujo de conversación ===
    if (nueva_noticia.get(tid) is not None or
        nuevo_sitio.get(tid) is not None or
        context.user_data):

        logger.info(f"[VOZ] Audio detectado DENTRO de un flujo (usuario {tid})")
        return   # Dejar que los handlers específicos (noticia_titulo_voz, etc.) lo procesen

    # === PRIORIDAD 2: Voz global (comandos como "agregar sitio", "stats", etc.) ===
    logger.info(f"[VOZ GLOBAL] Usuario {tid} dijo: '{update.message.voice}'")

    procesando_msg = await update.message.reply_text("🎙️ Procesando voz global...")

    try:
        voice_file = await update.message.voice.get_file()
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            tmp_path = tmp.name
        await voice_file.download_to_drive(tmp_path)

        texto = await _transcribir_audio(tmp_path)
        os.unlink(tmp_path)

        logger.info(f"[VOZ GLOBAL] Transcrito: {texto!r}")

        await procesando_msg.edit_text(f"🎙️ Escuché: _{texto}_", parse_mode="Markdown")

        accion = _detectar_intencion(texto)
        if not accion:
            await procesando_msg.edit_text(
                f"🎙️ Escuché: _{texto}_\n\n❓ No entendí la acción.\n"
                "Prueba diciendo: agregar sitio, publicar noticia, ver estadísticas, etc."
            )
            return

        await procesando_msg.delete()
        await _ejecutar_accion_por_voz(update, context, accion, usuario)

    except Exception as e:
        logger.error(f"Error voz global: {e}")
        await procesando_msg.edit_text(f"❌ Error procesando audio: {e}")


async def _ejecutar_accion_por_voz(update, context, accion: str, usuario):
    """Ejecuta una acción a partir de una intención detectada por voz."""
    send = update.message.reply_text

    # Acciones que requieren iniciar un flujo de conversación
    flujos_con_comando = {
        "agregar_sitio":    sitio_inicio,
        "desactivar_sitio": desactivar_inicio,
        "agregar_noticia":  noticia_inicio,
    }

    if accion in flujos_con_comando:
        # Verificar permisos antes de iniciar el flujo
        if accion == "agregar_noticia" and not es_admin(usuario):
            await send("⛔ Solo los administradores pueden publicar noticias.")
            return
        if accion in ("agregar_sitio", "desactivar_sitio") and not puede_agregar_sitio(usuario):
            await send("⛔ Solo empresarios y administradores pueden gestionar sitios.")
            return
        # Iniciar el flujo directamente
        await flujos_con_comando[accion](update, context)
        return

    if accion == "logout":
        sesiones.pop(update.effective_user.id, None)
        await send("👋 Sesión cerrada. ¡Hasta pronto!")
        return

    if accion == "volver_menu":
        await send(
            "📋 *Menú Principal*",
            parse_mode="Markdown",
            reply_markup=menu_principal(usuario),
        )
        return

    # Para las acciones de stats/info, reutilizamos la lógica del button_handler
    # creando un fake callback query context
    await _responder_stat_por_voz(send, accion, usuario)


async def _responder_stat_por_voz(send_fn, accion: str, usuario):
    """Responde a una acción de estadísticas sin necesitar un CallbackQuery."""

    if accion == "mi_establecimiento":
        if not es_empresario(usuario):
            await send_fn("⛔ Solo disponible para empresarios.", reply_markup=BOTON_VOLVER)
            return
        ests = await sync_to_async(_establecimientos_empresario, thread_sensitive=True)(usuario.pk)
        if not ests:
            await send_fn("📭 No tienes establecimientos activos.", reply_markup=BOTON_VOLVER)
            return
        texto = "🏢 *Tus Establecimientos Activos:*\n\n"
        for est in ests:
            texto += (
                f"📍 *{est.nombre}*\n"
                f"   Tipo: {est.tipo.nombre}\n"
                f"   Dirección: {est.direccion}\n"
                f"   Horario: {est.horario_aten}\n\n"
            )
        await send_fn(texto, parse_mode="Markdown", reply_markup=BOTON_VOLVER)

    elif accion == "mis_resenas":
        if not es_empresario(usuario):
            await send_fn("⛔ Solo disponible para empresarios.", reply_markup=BOTON_VOLVER)
            return
        datos = await sync_to_async(_resenas_por_establecimiento, thread_sensitive=True)(usuario.pk)
        texto = "⭐ *Reseñas de tus Establecimientos:*\n\n"
        for d in datos:
            promedio_str = f"{d['promedio']:.1f}" if d['promedio'] else "Sin calificaciones"
            dist_str = " | ".join([f"{i}★:{d['dist'][i]}" for i in range(5, 0, -1)])
            texto += (
                f"🏢 *{d['nombre']}*\n"
                f"   Total: {d['total']}  |  Promedio: {promedio_str} ⭐\n"
                f"   Distribución: {dist_str}\n\n"
            )
        await send_fn(texto, parse_mode="Markdown", reply_markup=BOTON_VOLVER)

    elif accion == "mis_favoritos":
        if not es_empresario(usuario):
            await send_fn("⛔ Solo disponible para empresarios.", reply_markup=BOTON_VOLVER)
            return
        datos = await sync_to_async(_favoritos_por_establecimiento, thread_sensitive=True)(usuario.pk)
        texto = "❤️ *Favoritos de tus Establecimientos:*\n\n"
        for d in datos:
            texto += f"🏢 *{d['nombre']}*: {d['total']} personas lo han guardado ❤️\n"
        if not datos:
            texto += "No tienes establecimientos registrados."
        await send_fn(texto, parse_mode="Markdown", reply_markup=BOTON_VOLVER)

    elif accion == "resumen_empresario":
        if not es_empresario(usuario):
            await send_fn("⛔ Solo disponible para empresarios.", reply_markup=BOTON_VOLVER)
            return
        d = await sync_to_async(_resumen_empresario, thread_sensitive=True)(usuario.pk)
        promedio_str = f"{d['promedio_global']:.1f}" if d['promedio_global'] else "N/A"
        mejor_str = f"{d['mejor_nombre']} ({d['mejor_avg']:.1f}⭐)" if d['mejor_nombre'] else "N/A"
        texto = (
            f"📊 *Resumen de tu Negocio*\n\n"
            f"🏢 Establecimientos: {d['total_est']} ({d['activos']} activos)\n"
            f"⭐ Total reseñas: {d['total_resenas']}\n"
            f"📈 Calificación promedio: {promedio_str} ⭐\n"
            f"❤️ Guardado en favoritos: {d['total_favoritos']}\n"
            f"🏆 Mejor calificado: {mejor_str}\n"
        )
        await send_fn(texto, parse_mode="Markdown", reply_markup=BOTON_VOLVER)

    elif accion == "stats_globales":
        if not es_admin(usuario):
            await send_fn("⛔ Solo disponible para administradores.", reply_markup=BOTON_VOLVER)
            return
        d = await sync_to_async(_stats_globales, thread_sensitive=True)()
        promedio_str = f"{d['promedio_global']:.2f}" if d['promedio_global'] else "N/A"
        texto = (
            f"📈 *Estadísticas Globales de PopayanAllTour*\n\n"
            f"👥 Usuarios activos: {d['total_usuarios']}\n"
            f"🧑‍💼 Empresarios: {d['total_empresarios']}\n"
            f"🏢 Establecimientos: {d['total_establecimientos']} ({d['est_activos']} activos)\n"
            f"⭐ Reseñas totales: {d['total_resenas']}\n"
            f"📊 Calificación promedio global: {promedio_str} ⭐\n"
            f"📰 Noticias publicadas: {d['total_noticias']}\n"
            f"❤️ Favoritos guardados: {d['total_favoritos']}\n"
        )
        await send_fn(texto, parse_mode="Markdown", reply_markup=BOTON_VOLVER)

    elif accion == "top_establecimientos":
        if not es_admin(usuario):
            await send_fn("⛔ Solo disponible para administradores.", reply_markup=BOTON_VOLVER)
            return
        top = await sync_to_async(_top_establecimientos, thread_sensitive=True)()
        if not top:
            await send_fn("📭 No hay establecimientos con datos aún.", reply_markup=BOTON_VOLVER)
            return
        texto = "🏆 *Top 10 Establecimientos*\n\n"
        for i, est in enumerate(top, 1):
            avg = f"{est.avg_cal:.1f}" if est.avg_cal else "Sin reseñas"
            texto += (
                f"{i}. *{est.nombre}*\n"
                f"   {avg} ⭐ | {est.total_resenas} reseñas | ❤️ {est.total_fav}\n\n"
            )
        await send_fn(texto, parse_mode="Markdown", reply_markup=BOTON_VOLVER)

    elif accion == "stats_noticias":
        if not es_admin(usuario):
            await send_fn("⛔ Solo disponible para administradores.", reply_markup=BOTON_VOLVER)
            return
        d = await sync_to_async(_stats_noticias, thread_sensitive=True)()
        texto = (
            f"📰 *Estadísticas de Noticias*\n\n"
            f"📄 Total noticias: {d['total']}\n"
            f"✅ Publicadas: {d['publicadas']}\n"
            f"🌟 Destacadas: {d['destacadas']}\n"
            f"👁️ Visitas totales: {d['total_visitas']:,}\n"
            f"❤️ Guardadas en favoritos: {d['total_fav']}\n\n"
            f"*📊 Top 5 más visitadas:*\n"
        )
        for i, (titulo, visitas) in enumerate(d['top'], 1):
            texto += f"{i}. {titulo[:40]} — {visitas:,} visitas\n"
        await send_fn(texto, parse_mode="Markdown", reply_markup=BOTON_VOLVER)

    elif accion == "stats_usuarios":
        if not es_admin(usuario):
            await send_fn("⛔ Solo disponible para administradores.", reply_markup=BOTON_VOLVER)
            return
        d = await sync_to_async(_stats_usuarios, thread_sensitive=True)()
        texto = (
            f"👥 *Estadísticas de Usuarios*\n\n"
            f"Total activos: {d['total']}\n\n"
            f"*Por Rol:*\n"
        )
        for r in d['por_rol']:
            texto += f"  • {r['rol__rol']}: {r['total']}\n"
        if d['por_tipo']:
            texto += "\n*Empresarios por Tipo de Negocio:*\n"
            for t in d['por_tipo']:
                texto += f"  • {t['tipo_establecimiento__nombre']}: {t['total']}\n"
        await send_fn(texto, parse_mode="Markdown", reply_markup=BOTON_VOLVER)


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS DE VOZ PARA FLUJOS DE CONVERSACIÓN
# ══════════════════════════════════════════════════════════════════════════════

async def _transcribir_voz_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str | None:
    try:
        if not update.message.voice:
            return None

        procesando = await update.message.reply_text("🎙️ Transcribiendo tu audio...")

        voice_file = await update.message.voice.get_file()
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            tmp_path = tmp.name
        await voice_file.download_to_drive(tmp_path)

        texto = await _transcribir_audio(tmp_path)
        os.unlink(tmp_path)

        await procesando.edit_text(f"✅ **Entendí:** _{texto}_", parse_mode="Markdown")
        return texto

    except Exception as e:
        logger.error(f"Error transcribiendo voz en flujo: {e}")
        await update.message.reply_text("❌ No pude transcribir el audio. Intenta de nuevo o escríbelo.")
        return None


# ====================== VOZ PARA NOTICIA ======================
async def noticia_titulo_voz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = await _transcribir_voz_mensaje(update, context)
    if not texto:
        return NEWS_TITULO

    message_data = update.message.to_dict() if update.message else {}
    message_data['text'] = texto.strip()
    fake_message = telegram.Message.de_json(message_data, update.get_bot())

    fake_update = Update(update_id=update.update_id + 1, message=fake_message)
    return await noticia_titulo(fake_update, context)


async def noticia_subtitulo_voz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = await _transcribir_voz_mensaje(update, context)
    if not texto:
        return NEWS_SUBTITULO

    message_data = update.message.to_dict() if update.message else {}
    message_data['text'] = texto.strip()
    fake_message = telegram.Message.de_json(message_data, update.get_bot())

    fake_update = Update(update_id=update.update_id + 1, message=fake_message)
    return await noticia_subtitulo(fake_update, context)


async def noticia_resumen_voz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = await _transcribir_voz_mensaje(update, context)
    if not texto:
        return NEWS_RESUMEN

    message_data = update.message.to_dict() if update.message else {}
    message_data['text'] = texto.strip()[:500]
    fake_message = telegram.Message.de_json(message_data, update.get_bot())

    fake_update = Update(update_id=update.update_id + 1, message=fake_message)
    return await noticia_resumen(fake_update, context)


async def noticia_contenido_voz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = await _transcribir_voz_mensaje(update, context)
    if not texto:
        return NEWS_CONTENIDO

    message_data = update.message.to_dict() if update.message else {}
    message_data['text'] = texto.strip()
    fake_message = telegram.Message.de_json(message_data, update.get_bot())

    fake_update = Update(update_id=update.update_id + 1, message=fake_message)
    return await noticia_contenido(fake_update, context)

# ====================== VOZ PARA AGREGAR SITIO ======================
async def sitio_nombre_voz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = await _transcribir_voz_mensaje(update, context)
    if not texto:
        return SITE_NOMBRE

    message_data = update.message.to_dict() if update.message else {}
    message_data['text'] = texto.strip()
    fake_message = telegram.Message.de_json(message_data, update.get_bot())

    fake_update = Update(update_id=update.update_id + 1, message=fake_message)
    return await sitio_nombre(fake_update, context)


async def sitio_descripcion_voz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = await _transcribir_voz_mensaje(update, context)
    if not texto:
        return SITE_DESCRIPCION

    message_data = update.message.to_dict() if update.message else {}
    message_data['text'] = texto.strip()
    fake_message = telegram.Message.de_json(message_data, update.get_bot())

    fake_update = Update(update_id=update.update_id + 1, message=fake_message)
    return await sitio_descripcion(fake_update, context)


async def sitio_direccion_voz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = await _transcribir_voz_mensaje(update, context)
    if not texto:
        return SITE_DIRECCION

    message_data = update.message.to_dict() if update.message else {}
    message_data['text'] = texto.strip()
    fake_message = telegram.Message.de_json(message_data, update.get_bot())

    fake_update = Update(update_id=update.update_id + 1, message=fake_message)
    return await sitio_direccion(fake_update, context)


async def sitio_horario_voz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = await _transcribir_voz_mensaje(update, context)
    if not texto:
        return SITE_HORARIO

    message_data = update.message.to_dict() if update.message else {}
    message_data['text'] = texto.strip()
    fake_message = telegram.Message.de_json(message_data, update.get_bot())

    fake_update = Update(update_id=update.update_id + 1, message=fake_message)
    return await sitio_horario(fake_update, context)


async def sitio_url_voz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = await _transcribir_voz_mensaje(update, context)
    if not texto:
        return SITE_URL

    message_data = update.message.to_dict() if update.message else {}
    message_data['text'] = texto.strip()
    fake_message = telegram.Message.de_json(message_data, update.get_bot())

    fake_update = Update(update_id=update.update_id + 1, message=fake_message)
    return await sitio_url(fake_update, context)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # ── Login ──────────────────────────────────────────────────────────────────
    login_handler = ConversationHandler(
        entry_points=[CommandHandler("login", login_start)],
        states={
            LOGIN_EMAIL:    [MessageHandler(filters.TEXT & ~filters.COMMAND, login_recibir_email)],
            LOGIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_recibir_password)],
        },
        fallbacks=[CommandHandler("cancel", login_cancel)],
    )

    # ── Agregar sitio ──────────────────────────────────────────────────────────
    agregar_handler = ConversationHandler(
        entry_points=[CommandHandler("agregar", sitio_inicio)],
        states={
            SITE_NOMBRE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, sitio_nombre),
                MessageHandler(filters.VOICE, sitio_nombre_voz),
            ],
            SITE_DESCRIPCION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, sitio_descripcion),
                MessageHandler(filters.VOICE, sitio_descripcion_voz),
            ],
            SITE_DIRECCION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, sitio_direccion),
                MessageHandler(filters.VOICE, sitio_direccion_voz),
            ],
            SITE_HORARIO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, sitio_horario),
                MessageHandler(filters.VOICE, sitio_horario_voz),
            ],
            SITE_TIPO: [CallbackQueryHandler(sitio_tipo, pattern="^tipo_")],
            SITE_URL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, sitio_url),
                MessageHandler(filters.VOICE, sitio_url_voz),
            ],
            SITE_IMAGEN: [
                MessageHandler(filters.PHOTO, sitio_imagen_recibida),
                CallbackQueryHandler(sitio_imagen_omitida, pattern="^omitir_imagen_sitio$"),
            ],
            SITE_CONFIRMAR: [CallbackQueryHandler(sitio_confirmar, pattern="^confirmar_sitio$")],
        },
        fallbacks=[CommandHandler("cancelar", cancelar_flujo),
                   CallbackQueryHandler(cancelar_flujo, pattern="^cancelar_flujo$")],
    )

    # ── Desactivar sitio ───────────────────────────────────────────────────────
    desactivar_handler = ConversationHandler(
        entry_points=[CommandHandler("desactivar", desactivar_inicio)],
        states={
            DESACT_ELEGIR:    [CallbackQueryHandler(desactivar_elegido,   pattern=r"^desact_\d+$")],
            DESACT_CONFIRMAR: [CallbackQueryHandler(desactivar_confirmar, pattern="^confirmar_desact$")],
        },
        fallbacks=[
            CommandHandler("cancelar", cancelar_flujo),
            CallbackQueryHandler(cancelar_flujo, pattern="^cancelar_flujo$"),
        ],
    )

    # ── Agregar noticia ────────────────────────────────────────────────────────
    noticia_handler = ConversationHandler(
        entry_points=[CommandHandler("noticia", noticia_inicio)],
        states={
            NEWS_TITULO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, noticia_titulo),
                MessageHandler(filters.VOICE, noticia_titulo_voz),
            ],
            NEWS_SUBTITULO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, noticia_subtitulo),
                MessageHandler(filters.VOICE, noticia_subtitulo_voz),
                CallbackQueryHandler(noticia_subtitulo_omitido, pattern="^omitir_subtitulo$"),
            ],
            NEWS_RESUMEN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, noticia_resumen),
                MessageHandler(filters.VOICE, noticia_resumen_voz),
                CallbackQueryHandler(noticia_resumen_omitido, pattern="^omitir_resumen$"),
            ],
            NEWS_CONTENIDO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, noticia_contenido),
                MessageHandler(filters.VOICE, noticia_contenido_voz),
            ],
            NEWS_CATEGORIA: [CallbackQueryHandler(noticia_categoria, pattern="^cat_")],
            NEWS_IMAGEN: [
                MessageHandler(filters.PHOTO, noticia_imagen_recibida),
                CallbackQueryHandler(noticia_imagen_omitida, pattern="^omitir_imagen_noticia$"),
            ],
            NEWS_DESTACADA: [CallbackQueryHandler(noticia_destacada, pattern="^noticia_destacada_")],
            NEWS_CONFIRMAR: [CallbackQueryHandler(noticia_confirmar, pattern="^confirmar_noticia$")],
        },
        fallbacks=[
            CommandHandler("cancelar", cancelar_flujo),
            CallbackQueryHandler(cancelar_flujo, pattern="^cancelar_flujo$"),
        ],
    )

    # ── Registro (orden importa: ConversationHandlers antes que button_handler) ─
    app.add_handler(CommandHandler("start",      start))
    app.add_handler(CommandHandler("ayuda",      ayuda))
    app.add_handler(CommandHandler("help",       ayuda))
    app.add_handler(CommandHandler("menu",       cmd_menu))
    app.add_handler(CommandHandler("logout",     logout_cmd))
    app.add_handler(login_handler)
    app.add_handler(agregar_handler)
    app.add_handler(desactivar_handler)
    app.add_handler(noticia_handler)
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.VOICE, voice_handler))

    logger.info("🤖 Bot PopayanAllTour iniciado...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()