// ============================================
// NAVBAR SCROLL EFFECT
// ============================================
window.addEventListener('scroll', function() {
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    }
});

// ============================================
// SMOOTH SCROLL FOR ANCHOR LINKS
// ============================================
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// ============================================
// INTERSECTION OBSERVER FOR ANIMATIONS
// ============================================
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver(function(entries) {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// ============================================
// DOCUMENT READY - INICIALIZACIÓN PRINCIPAL
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    
    // INICIALIZAR ANIMACIONES DE SECCIONES
    const sections = document.querySelectorAll('section');
    sections.forEach(section => {
        section.style.opacity = '0';
        section.style.transform = 'translateY(30px)';
        section.style.transition = 'all 0.8s ease-out';
        observer.observe(section);
    });
    
    // ============================================
    // MENÚ HAMBURGUESA (MISMO DISEÑO QUE HOME.JS)
    // ============================================
    const hamburger = document.getElementById('hamburger');
    const navMenu = document.getElementById('nav-menu');
    
    if (hamburger && navMenu) {
        hamburger.addEventListener('click', function() {
            navMenu.classList.toggle('active');
        });
        
        // Cerrar menú al hacer click en un enlace
        document.querySelectorAll('.nav-menu a').forEach(link => {
            link.addEventListener('click', () => {
                navMenu.classList.remove('active');
            });
        });
    }
    
    // ============================================
    // MENÚ DESPLEGABLE DE USUARIO
    // ============================================
    const userIconHome = document.getElementById("userIconHome");
    const dropdownMenuHome = document.getElementById("dropdownMenuHome");
    const logoutModalHome = document.getElementById("logoutModalHome");
    const logoutBtnHome = document.getElementById("logoutBtnHome");
    const cancelLogoutHome = document.getElementById("cancelLogoutHome");
    const closeHome = document.querySelector(".close-home");

    if (userIconHome && dropdownMenuHome) {
        userIconHome.addEventListener("click", function(e) {
            e.preventDefault();
            e.stopPropagation();
            dropdownMenuHome.classList.toggle("open");
        });

        document.addEventListener("click", function(e) {
            if (!dropdownMenuHome.contains(e.target) && !userIconHome.contains(e.target)) {
                dropdownMenuHome.classList.remove("open");
            }
        });

        dropdownMenuHome.addEventListener("click", function(e) {
            e.stopPropagation();
        });
    }

    if (logoutBtnHome && logoutModalHome) {
        logoutBtnHome.addEventListener("click", function(e) {
            e.preventDefault();
            e.stopPropagation();
            if (dropdownMenuHome) {
                dropdownMenuHome.classList.remove("open");
            }
            logoutModalHome.style.display = "block";
        });
    }

    if (cancelLogoutHome && logoutModalHome) {
        cancelLogoutHome.addEventListener("click", function(e) {
            e.preventDefault();
            logoutModalHome.style.display = "none";
        });
    }

    if (closeHome && logoutModalHome) {
        closeHome.addEventListener("click", function(e) {
            e.preventDefault();
            logoutModalHome.style.display = "none";
        });
    }

    if (logoutModalHome) {
        window.addEventListener("click", function(event) {
            if (event.target === logoutModalHome) {
                logoutModalHome.style.display = "none";
            }
        });
    }

    // ============================================
    // DETECTAR ERRORES DE CARGA DE IMÁGENES
    // ============================================
    const images = document.querySelectorAll('img');
    images.forEach(img => {
        img.addEventListener('error', function() {
            console.error('Error al cargar imagen:', this.src);
            // Opcional: poner una imagen placeholder
            // this.src = '/static/img/placeholder.png';
        });
        
        img.addEventListener('load', function() {
            console.log('Imagen cargada correctamente:', this.src);
        });
    });

    console.log('Historia.js cargado correctamente');
});