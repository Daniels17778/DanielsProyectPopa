

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
  // NAVBAR CON SCROLL
  // ============================================
  const navbar = document.getElementById("navbar");

  window.addEventListener("scroll", function () {
    if (navbar) {
      if (window.scrollY > 50) {
        navbar.classList.add("scrolled");
      } else {
        navbar.classList.remove("scrolled");
      }
    }
  });



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