// ============================================================
// PERFIL DE USUARIO - FUNCIONALIDADES
// ============================================================

document.addEventListener('DOMContentLoaded', function() {
    
    // ============================================================
    // 1. NAVBAR SCROLL EFFECT
    // ============================================================
    const navbar = document.getElementById('navbar');
    const hamburger = document.getElementById('hamburger');
    const navMenu = document.getElementById('nav-menu');

    window.addEventListener('scroll', function() {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    // Toggle menú móvil
    if (hamburger && navMenu) {
        hamburger.addEventListener('click', function() {
            navMenu.classList.toggle('show');
        });
    }

    // ============================================================
    // 2. MANEJO DE IMAGEN DE PERFIL
    // ============================================================
    
    const fileInput = document.getElementById('fileInput');
    const profileImage = document.getElementById('profileImage');
    const uploadBtn = document.querySelector('.upload-btn');
    
    // Función para previsualizar imagen
    window.handleImageUpload = function(event) {
        const file = event.target.files[0];
        
        if (file) {
            // Validar tamaño (máximo 5MB)
            if (file.size > 5 * 1024 * 1024) {
                alert('❌ La imagen no puede ser mayor a 5MB');
                event.target.value = '';
                return;
            }
            
            // Validar tipo de archivo
            const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
            if (!validTypes.includes(file.type)) {
                alert('❌ Solo se permiten imágenes (JPG, PNG, GIF, WEBP)');
                event.target.value = '';
                return;
            }
            
            // Crear preview
            const reader = new FileReader();
            reader.onload = function(e) {
                profileImage.innerHTML = `
                    <img src="${e.target.result}" 
                         alt="Preview" 
                         style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">
                `;
            };
            reader.readAsDataURL(file);
            
            console.log('✅ Imagen cargada:', file.name);
        }
    };
    
    // ============================================================
    // 3. RESETEAR IMAGEN (ELIMINAR)
    // ============================================================
    
    window.resetImage = function() {
        if (confirm('¿Estás seguro de que deseas eliminar tu imagen de perfil?')) {
            // Limpiar el input
            if (fileInput) {
                fileInput.value = '';
            }
            
            // Enviar solicitud para eliminar imagen del servidor
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/eliminar-imagen-perfil/';
            
            // Agregar CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            const csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrfmiddlewaretoken';
            csrfInput.value = csrfToken;
            form.appendChild(csrfInput);
            
            document.body.appendChild(form);
            form.submit();
        }
    };
    
    // ============================================================
    // 4. MOSTRAR/OCULTAR TIPO DE ESTABLECIMIENTO SEGÚN ROL
    // ============================================================
    
    window.toggleTipoEstablecimiento = function() {
        const rolSelect = document.getElementById('id_rol');
        const tipoEstablecimientoGroup = document.getElementById('tipoEstablecimientoGroup');
        
        if (rolSelect && tipoEstablecimientoGroup) {
            // Obtener el texto del rol seleccionado
            const selectedOption = rolSelect.options[rolSelect.selectedIndex];
            const selectedRolText = selectedOption ? selectedOption.text.toLowerCase() : '';
            
            if (selectedRolText === 'empresario') {
                tipoEstablecimientoGroup.style.display = 'block';
            } else {
                tipoEstablecimientoGroup.style.display = 'none';
            }
        }
    };
    
    // Ejecutar al cargar la página
    toggleTipoEstablecimiento();
    
    // ============================================================
    // 5. CONFIRMACIÓN DE ELIMINACIÓN DE CUENTA
    // ============================================================
    
    window.confirmDelete = function() {
        const confirmText = prompt(
            '⚠️ ADVERTENCIA: Esta acción es irreversible.\n\n' +
            'Todos tus datos serán eliminados permanentemente.\n\n' +
            'Para confirmar, escribe: ELIMINAR'
        );
        
        if (confirmText === 'ELIMINAR') {
            // Crear formulario para enviar solicitud de eliminación
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = window.location.href;
            
            // CSRF Token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            const csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrfmiddlewaretoken';
            csrfInput.value = csrfToken;
            form.appendChild(csrfInput);
            
            // Action field
            const actionInput = document.createElement('input');
            actionInput.type = 'hidden';
            actionInput.name = 'action';
            actionInput.value = 'delete';
            form.appendChild(actionInput);
            
            // Submit
            document.body.appendChild(form);
            form.submit();
        } else if (confirmText !== null) {
            alert('❌ Texto incorrecto. La cuenta no fue eliminada.');
        }
    };
    
    // ============================================================
    // 6. VALIDACIÓN EN TIEMPO REAL
    // ============================================================
    
    // Validar email
    const emailInput = document.querySelector('input[type="email"]');
    if (emailInput) {
        emailInput.addEventListener('blur', function() {
            const email = this.value;
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            
            if (email && !emailRegex.test(email)) {
                this.style.borderColor = '#dc3545';
                showError(this, 'Email inválido');
            } else {
                this.style.borderColor = '#333333';
                hideError(this);
            }
        });
    }
    
    // Validar teléfono
    const phoneInput = document.querySelector('input[type="tel"]');
    if (phoneInput) {
        phoneInput.addEventListener('blur', function() {
            const phone = this.value.replace(/\s/g, '');
            
            if (phone && phone.length < 7) {
                this.style.borderColor = '#dc3545';
                showError(this, 'El teléfono debe tener al menos 7 dígitos');
            } else {
                this.style.borderColor = '#333333';
                hideError(this);
            }
        });
    }
    
    // Validar contraseñas coincidan
    const newPasswordInput = document.querySelector('input[name="nueva_password"]');
    const confirmPasswordInput = document.querySelector('input[name="confirmar_password"]');
    
    if (newPasswordInput && confirmPasswordInput) {
        confirmPasswordInput.addEventListener('blur', function() {
            if (this.value && this.value !== newPasswordInput.value) {
                this.style.borderColor = '#dc3545';
                showError(this, 'Las contraseñas no coinciden');
            } else {
                this.style.borderColor = '#333333';
                hideError(this);
            }
        });
    }
    
    // ============================================================
    // 7. FUNCIONES AUXILIARES
    // ============================================================
    
    function showError(element, message) {
        // Remover error anterior si existe
        hideError(element);
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.style.color = '#dc3545';
        errorDiv.style.fontSize = '12px';
        errorDiv.style.marginTop = '5px';
        errorDiv.textContent = message;
        
        element.parentNode.appendChild(errorDiv);
    }
    
    function hideError(element) {
        const errorMsg = element.parentNode.querySelector('.error-message');
        if (errorMsg) {
            errorMsg.remove();
        }
    }
    
    // ============================================================
    // 8. PREVENIR ENVÍO MÚLTIPLE DEL FORMULARIO
    // ============================================================
    
    const saveBtn = document.querySelector('.save-btn');
    const form = document.querySelector('form');
    
    if (form && saveBtn) {
        form.addEventListener('submit', function() {
            saveBtn.disabled = true;
            saveBtn.textContent = 'Guardando...';
            saveBtn.style.opacity = '0.6';
        });
    }
    
    // ============================================================
    // 9. MENSAJE DE CONFIRMACIÓN AL SALIR SIN GUARDAR
    // ============================================================
    
    let formChanged = false;
    
    if (form) {
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('change', function() {
                formChanged = true;
            });
        });
        
        window.addEventListener('beforeunload', function(e) {
            if (formChanged) {
                e.preventDefault();
                e.returnValue = '';
            }
        });
        
        form.addEventListener('submit', function() {
            formChanged = false;
        });
    }
    
    console.log('✅ Perfil de usuario cargado correctamente');
});

// Botón Volver
document.getElementById('backButton').addEventListener('click', function(e) {
    e.preventDefault();
    
    if (window.history.length > 1) {
        window.history.back();
    } else {
        window.location.href = '/'; // URL de respaldo
    }
});