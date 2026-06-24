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
// HISTORY CAROUSEL VARIABLES
// ============================================
let historySlideIndex = 1;
let historySlideInterval;

// ============================================
// HISTORY CAROUSEL FUNCTIONS
// ============================================
function initHistoryCarousel() {
    showHistorySlide(historySlideIndex);
    startHistoryAutoSlide();
    setupHistoryNavigationEvents();
}

function setupHistoryNavigationEvents() {
    const prevBtn = document.querySelector('#historia .carousel-nav.prev');
    const nextBtn = document.querySelector('#historia .carousel-nav.next');
    
    if (prevBtn) {
        prevBtn.addEventListener('click', () => changeHistorySlide(-1));
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', () => changeHistorySlide(1));
    }
    
    const dots = document.querySelectorAll('#historia .carousel-dots .dot');
    dots.forEach((dot, index) => {
        dot.addEventListener('click', () => goToHistorySlide(index + 1));
    });
}

function changeHistorySlide(direction) {
    historySlideIndex += direction;
    
    const historyCarousel = document.querySelector('#historia');
    if (!historyCarousel) return;
    
    const totalSlides = historyCarousel.querySelectorAll('.carousel-slide').length;
    
    if (historySlideIndex > totalSlides) {
        historySlideIndex = 1;
    } else if (historySlideIndex < 1) {
        historySlideIndex = totalSlides;
    }
    
    showHistorySlide(historySlideIndex);
    resetHistoryAutoSlide();
}

function goToHistorySlide(index) {
    historySlideIndex = index;
    showHistorySlide(historySlideIndex);
    resetHistoryAutoSlide();
}

function showHistorySlide(index) {
    const historyCarousel = document.querySelector('#historia');
    if (!historyCarousel) return;
    
    const slides = historyCarousel.querySelectorAll('.carousel-slide');
    const dots = historyCarousel.querySelectorAll('.dot');
    
    slides.forEach(slide => slide.classList.remove('active'));
    dots.forEach(dot => dot.classList.remove('active'));
    
    if (slides[index - 1]) {
        slides[index - 1].classList.add('active');
        dots[index - 1].classList.add('active');
    }
}

function startHistoryAutoSlide() {
    historySlideInterval = setInterval(function() {
        changeHistorySlide(1);
    }, 6000);
}

function resetHistoryAutoSlide() {
    clearInterval(historySlideInterval);
    startHistoryAutoSlide();
}

function setupHistoryCarouselEvents() {
    const carousel = document.querySelector('#historia');
    if (!carousel) return;

    carousel.addEventListener('mouseenter', function() {
        clearInterval(historySlideInterval);
    });

    carousel.addEventListener('mouseleave', function() {
        startHistoryAutoSlide();
    });

    let touchStartX = 0;
    let touchEndX = 0;

    carousel.addEventListener('touchstart', function(e) {
        touchStartX = e.changedTouches[0].screenX;
    });

    carousel.addEventListener('touchend', function(e) {
        touchEndX = e.changedTouches[0].screenX;
        handleHistorySwipe();
    });

    function handleHistorySwipe() {
        const swipeThreshold = 50;
        const diff = touchStartX - touchEndX;
        
        if (Math.abs(diff) > swipeThreshold) {
            if (diff > 0) {
                changeHistorySlide(1);
            } else {
                changeHistorySlide(-1);
            }
        }
    }
}

// ============================================
// MODAL FUNCTIONS (GLOBAL)
// ============================================
window.openHistoryModal = function(type) {
    const modal = document.getElementById('historyModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalIcon = document.getElementById('modalIcon');
    const modalBody = document.getElementById('modalBody');
    
    const content = {
        fundacion: {
            icon: '⛪',
            title: '1537 - Fundación de Popayán',
            body: `
                <div class="info-section">
                    <h3>Los Primeros Días</h3>
                    <p><span class="highlight">15 de agosto de 1537</span> - Día de La Asunción: Primera vez que se dio culto a Dios en la recién fundada ciudad de Popayán, según documenta el presbítero e historiador Manuel A. Bueno.</p>
                    
                    <h3>Contexto Histórico</h3>
                    <ul class="info-list">
                        <li>• Popayán fue fundada por Sebastián de Belalcázar</li>
                        <li>• Ubicada estratégicamente en el Valle de Pubenza</li>
                        <li>• Centro de poder colonial en el sur del Virreinato</li>
                        <li>• Los primeros templos se construyeron de inmediato</li>
                    </ul>
                </div>
                <div class="info-section">
                    <h3>Importancia Religiosa</h3>
                    <p>Desde sus primeros meses, Popayán se estableció como un centro de profunda religiosidad, sentando las bases para lo que siglos después se convertiría en una de las tradiciones más importantes de América Latina.</p>
                </div>
            `
        },
        procesiones: {
            icon: '🚶‍♂️',
            title: '1556 - Inicio de las Procesiones',
            body: `
                <div class="info-section">
                    <h3>El Comienzo de una Tradición</h3>
                    <p><span class="highlight">Año 1556</span> - Las Procesiones de Semana Santa de Popayán inician como muestra religiosa en conmemoración de la pasión, muerte y resurrección de Jesús.</p>
                </div>
            `
        },
        bolivar: {
            icon: '⚔️',
            title: '1826 - Procesión en Honor a Bolívar',
            body: `
                <div class="info-section">
                    <h3>El Libertador en Popayán</h3>
                    <p><span class="highlight">Última semana de octubre de 1826</span> - Simón Bolívar regresa triunfante después de la batalla de Ayacucho.</p>
                </div>
            `
        },
        supremos: {
            icon: '⚔️',
            title: '1840 - Los Supremos Participan',
            body: `
                <div class="info-section">
                    <h3>Un Momento Histórico</h3>
                    <p><span class="highlight">14 de abril de 1840</span> - José María Obando y Juan Gregorio Sarria participan en la procesión.</p>
                </div>
            `
        },
        vergara: {
            icon: '📖',
            title: '1859 - Descripción de Vergara y Vergara',
            body: `
                <div class="info-section">
                    <h3>El Cronista José María Vergara y Vergara</h3>
                    <p><span class="highlight">Año 1859</span> - Descripción histórica de las procesiones.</p>
                </div>
            `
        },
        terremoto: {
            icon: '🌍',
            title: '1983 - El Terremoto',
            body: `
                <div class="info-section">
                    <h3>El Día que Todo Cambió</h3>
                    <p><span class="highlight">31 de marzo de 1983 - Jueves Santo</span> - Devastador terremoto en Popayán.</p>
                </div>
            `
        },
        unesco: {
            icon: '🏆',
            title: '2009 - Declaración UNESCO',
            body: `
                <div class="info-section">
                    <h3>Reconocimiento Mundial</h3>
                    <p><span class="highlight">2009</span> - Patrimonio Cultural Inmaterial de la Humanidad.</p>
                </div>
            `
        },
        pandemia: {
            icon: '🦠',
            title: '2020-2021 - Pandemia COVID-19',
            body: `
                <div class="info-section">
                    <h3>Segunda Suspensión Histórica</h3>
                    <p><span class="highlight">2020 y 2021</span> - Suspensión por pandemia mundial.</p>
                </div>
            `
        }
    };
    
    const selectedContent = content[type] || content.fundacion;
    modalIcon.textContent = selectedContent.icon;
    modalTitle.textContent = selectedContent.title;
    modalBody.innerHTML = selectedContent.body;
    
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
};

window.closeHistoryModal = function() {
    const modal = document.getElementById('historyModal');
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = 'auto';
    }
};

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
    
    // INICIALIZAR CARRUSEL DE HISTORIA
    const historyCarousel = document.querySelector('#historia');
    if (historyCarousel) {
        initHistoryCarousel();
        setupHistoryCarouselEvents();
    }
    
    // CERRAR MODAL AL HACER CLICK FUERA
    const historyModal = document.getElementById('historyModal');
    if (historyModal) {
        historyModal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeHistoryModal();
            }
        });
    }
    
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
});