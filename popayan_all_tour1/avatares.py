# avatares.py

AVATARES_PREDETERMINADOS = [
    {
        'id': 'avatar1',
        'nombre': 'Avatar Naranja',
        'url': 'https://res.cloudinary.com/de7ob8hb2/image/upload/v1768505287/avatar_naranja_ofufi8.png'
    },
    {
        'id': 'avatar2',
        'nombre': 'Avatar Azul',
        'url': 'https://res.cloudinary.com/de7ob8hb2/image/upload/v1768505286/avatar_azul_vxyccz.png'
    },
    {
        'id': 'avatar3',
        'nombre': 'Avatar Negro',
        'url': 'https://res.cloudinary.com/de7ob8hb2/image/upload/v1768505286/avatar_juandavid_yghsec.png'
    },
    {
        'id': 'avatar4',
        'nombre': 'Avatar Verde',
        'url': 'https://res.cloudinary.com/de7ob8hb2/image/upload/v1768505285/avatar_verde_p5c18v.png'
    },
    {
        'id': 'avatar5',
        'nombre': 'Avatar Morado',
        'url': 'https://res.cloudinary.com/de7ob8hb2/image/upload/v1768505286/avatar_morado_p2b7o6.png'
    },
    {
        'id': 'avatar6',
        'nombre': 'Avatar Blanco',
        'url': 'https://res.cloudinary.com/de7ob8hb2/image/upload/v1768505286/avatar_blanco_c5ka4q.png'
    },
    {
        'id': 'avatar7',
        'nombre': 'Avatar Amarillo',
        'url': 'https://res.cloudinary.com/de7ob8hb2/image/upload/v1768505285/avatar_amarillo_hcvzqs.png'
    },
    {
        'id': 'avatar8',
        'nombre': 'Avatar Rosado',
        'url': 'https://res.cloudinary.com/de7ob8hb2/image/upload/v1768505285/avatar_rosa_pol7zy.png'
    },
    {
        'id': 'avatar9',
        'nombre': 'Avatar Rojo',
        'url': 'https://res.cloudinary.com/de7ob8hb2/image/upload/v1768505285/avatar_rojo_ohf0io.png'
    },
]

def get_avatar_choices():
    """Devuelve lista de tuplas (id, nombre) para usar en formularios"""
    return [(avatar['id'], avatar['nombre']) for avatar in AVATARES_PREDETERMINADOS]

def get_avatar_url(avatar_id):
    """Obtiene la URL de un avatar por su ID"""
    for avatar in AVATARES_PREDETERMINADOS:
        if avatar['id'] == avatar_id:
            return avatar['url']
    return None