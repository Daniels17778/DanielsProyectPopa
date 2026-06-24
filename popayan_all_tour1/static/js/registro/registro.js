document.addEventListener("DOMContentLoaded", function () {
    // ============================================================
    // FUNCIONALIDAD EXISTENTE - Tipo de Establecimiento
    // ============================================================
    const rolField = document.getElementById("id_rol");
    const tipoEstablecimientoContainer = document.getElementById("tipo_establecimiento-container");
    const tipoEstablecimientoInput = document.getElementById("id_tipo_establecimiento");

    function toggleEstablecimiento() {
        const selectedText = rolField.options[rolField.selectedIndex].text.toLowerCase();
        if (selectedText === "empresario") {
            tipoEstablecimientoContainer.style.display = "block";
            tipoEstablecimientoInput.required = true;
        } else {
            tipoEstablecimientoContainer.style.display = "none";
            tipoEstablecimientoInput.required = false;
            tipoEstablecimientoInput.value = "";
        }
    }

    rolField.addEventListener("change", toggleEstablecimiento);
    toggleEstablecimiento();

    // ============================================================
    // NUEVA FUNCIONALIDAD - Carrusel de Avatares
    // ============================================================
    
    // Obtener avatares desde window.avataresList
    const avatares = window.avataresList || [];
    
    // Verificar que existan avatares
    if (avatares.length === 0) {
        console.error('No hay avatares disponibles');
        document.querySelector('.avatar-carousel-section').innerHTML = 
            '<p style="text-align: center; color: #999; padding: 20px;">No hay avatares disponibles</p>';
        return;
    }

    let currentIndex = 0;
    let selectedAvatarId = null;

    const currentAvatarImg = document.getElementById('currentAvatarImg');
    const avatarName = document.getElementById('avatarName');
    const avatarCounter = document.getElementById('avatarCounter');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const confirmAvatarBtn = document.getElementById('confirmAvatarBtn');
    const selectedAvatarInfo = document.getElementById('selectedAvatarInfo');
    const selectedAvatarName = document.getElementById('selectedAvatarName');
    const avatarInput = document.getElementById('avatarInput');

    // Función para actualizar la visualización del avatar
    function updateAvatar() {
        const avatar = avatares[currentIndex];
        currentAvatarImg.src = avatar.url;
        currentAvatarImg.onerror = function() {
            this.src = 'https://ui-avatars.com/api/?name=?&background=667eea&color=fff&size=400';
        };
        avatarName.textContent = avatar.nombre;
        avatarCounter.textContent = `${currentIndex + 1} / ${avatares.length}`;
    }

    // Botón anterior
    prevBtn.addEventListener('click', () => {
        currentIndex = (currentIndex - 1 + avatares.length) % avatares.length;
        updateAvatar();
    });

    // Botón siguiente
    nextBtn.addEventListener('click', () => {
        currentIndex = (currentIndex + 1) % avatares.length;
        updateAvatar();
    });

    // Botón confirmar avatar
    confirmAvatarBtn.addEventListener('click', () => {
        selectedAvatarId = avatares[currentIndex].id;
        selectedAvatarName.textContent = avatares[currentIndex].nombre;
        selectedAvatarInfo.classList.add('show');
        
        // Guardar el ID del avatar en el input oculto
        avatarInput.value = selectedAvatarId;
        
        console.log('Avatar seleccionado:', avatares[currentIndex]);
    });

    // Navegación con teclado (opcional)
    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft') {
            prevBtn.click();
        } else if (e.key === 'ArrowRight') {
            nextBtn.click();
        }
    });

    // Inicializar el primer avatar
    updateAvatar();
});