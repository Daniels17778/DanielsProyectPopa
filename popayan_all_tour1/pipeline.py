from django.contrib.auth import get_user_model
from django.shortcuts import redirect
import uuid

User = get_user_model()

def create_user(strategy, details, backend, user=None, *args, **kwargs):
    if user:
        return {'is_new': False}

    email = details.get('email')
    if not email:
        return

    try:
        existing = User.objects.get(email=email)
        return {'is_new': False, 'user': existing}
    except User.DoesNotExist:
        pass

    from popayan_all_tour1.models import Roles
    try:
        rol_turista = Roles.objects.get(rol__iexact='turista')
    except Roles.DoesNotExist:
        raise Exception("No existe el rol 'turista'. Créalo en el admin.")

    nombre = details.get('fullname') or \
             f"{details.get('first_name', '')} {details.get('last_name', '')}".strip() or \
             email.split('@')[0]

    u = User(
        email=email,
        nombre_completo=nombre,
        telefono='',
        identificacion=f"google-{uuid.uuid4().hex[:12]}",
        fecha_nacimiento='2000-01-01',  # placeholder, se reemplaza en completar_perfil
        direccion='',
        rol=rol_turista,
        is_active=True,
    )
    u.set_unusable_password()
    u.save()

    return {'is_new': True, 'user': u}


def redirect_to_complete_profile(strategy, details, backend, user=None, *args, **kwargs):
    """Si el usuario recién se creó con Google, redirige a completar perfil."""
    if not user:
        return

    is_new = kwargs.get('is_new', False)
    if is_new:
        return redirect('/completar-perfil/')