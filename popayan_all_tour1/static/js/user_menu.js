document.addEventListener("DOMContentLoaded", function () {
  // ============================================
  // SLIDER DE IMÁGENES DEL HERO
  // ============================================
  const slides = document.querySelectorAll(".slide");
  let currentSlide = 0;
  const totalSlides = slides.length;

  function showSlide(index) {
    slides.forEach((slide, i) => {
      slide.classList.toggle("active", i === index);
    });
  }

  if (slides.length > 0) {
    setInterval(() => {
      currentSlide = (currentSlide + 1) % totalSlides;
      showSlide(currentSlide);
    }, 6000);
  }

  // ============================================
  // MENÚ HAMBURGUESA
  // ============================================
  const hamburger = document.getElementById("hamburger");
  const navMenu = document.getElementById("nav-menu");

  if (hamburger && navMenu) {
    hamburger.addEventListener("click", () => {
      navMenu.classList.toggle("show");
    });
  }

  // ============================================
  // NAVBAR CON SCROLL
  // ============================================
  const navbar = document.getElementById("navbar");
  
  window.addEventListener('scroll', function() {
    if (navbar) {
      if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
      } else {
        navbar.classList.remove('scrolled');
      }
    }
  });

  // ============================================
  // CARRUSELES
  // ============================================
  const carrusel = document.getElementById('carrusel');
  const carrusel2 = document.getElementById('carrusel2');
  const carrusel3 = document.getElementById('carrusel3');
  const carrusel4 = document.getElementById('carrusel4');

  if (carrusel) {
    const slides = carrusel.innerHTML;
    carrusel.innerHTML += slides + slides;
  }
  
  if (carrusel2) {
    const slides2 = carrusel2.innerHTML;
    carrusel2.innerHTML += slides2 + slides2;
  }
  
  if (carrusel3) {
    const slides3 = carrusel3.innerHTML;
    carrusel3.innerHTML += slides3 + slides3;
  }
  
  if (carrusel4) {
    const slides4 = carrusel4.innerHTML;
    carrusel4.innerHTML += slides4 + slides4;
  }

  // ============================================
  // MODAL DE IMÁGENES
  // ============================================
  const modal = document.getElementById('modal');
  const imagenAmpliada = document.getElementById('imagenAmpliada');
  const cerrar = document.getElementById('cerrar');

  // Aplicar evento a todas las clases que comienzan con "slide"
  document.querySelectorAll('[class^="slide"]').forEach(slide => {
    const img = slide.querySelector('img');
    if (img) {
      slide.addEventListener('click', () => {
        imagenAmpliada.src = img.src;
        modal.style.display = 'block';
      });
    }
  });

  // Cerrar modal
  if (cerrar && modal) {
    cerrar.addEventListener('click', () => {
      modal.style.display = 'none';
    });

    modal.addEventListener('click', e => {
      if (e.target === modal) {
        modal.style.display = 'none';
      }
    });
  }

  // ============================================
  // MENÚ DESPLEGABLE DE USUARIO EN HOME
  // ============================================
  const userIconHome = document.getElementById("userIconHome");
  const dropdownMenuHome = document.getElementById("dropdownMenuHome");
  const logoutModalHome = document.getElementById("logoutModalHome");
  const logoutBtnHome = document.getElementById("logoutBtnHome");
  const cancelLogoutHome = document.getElementById("cancelLogoutHome");
  const closeHome = document.querySelector(".close-home");

  // Toggle dropdown cuando se hace clic en el icono de usuario
  if (userIconHome && dropdownMenuHome) {
    userIconHome.addEventListener("click", function(e) {
      e.preventDefault();
      e.stopPropagation();
      dropdownMenuHome.classList.toggle("open");
    });

    // Cerrar dropdown al hacer clic fuera
    document.addEventListener("click", function(e) {
      if (!dropdownMenuHome.contains(e.target) && !userIconHome.contains(e.target)) {
        dropdownMenuHome.classList.remove("open");
      }
    });

    // Prevenir que el dropdown se cierre al hacer clic dentro de él
    dropdownMenuHome.addEventListener("click", function(e) {
      e.stopPropagation();
    });
  }

  // Abrir modal de cerrar sesión
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

  // Cerrar modal con el botón cancelar
  if (cancelLogoutHome && logoutModalHome) {
    cancelLogoutHome.addEventListener("click", function(e) {
      e.preventDefault();
      logoutModalHome.style.display = "none";
    });
  }

  // Cerrar modal con la X
  if (closeHome && logoutModalHome) {
    closeHome.addEventListener("click", function(e) {
      e.preventDefault();
      logoutModalHome.style.display = "none";
    });
  }

  // Cerrar modal al hacer clic fuera de él
  if (logoutModalHome) {
    window.addEventListener("click", function(event) {
      if (event.target === logoutModalHome) {
        logoutModalHome.style.display = "none";
      }
    });
  }
});

const hamburger = document.getElementById("hamburger");
const navMenu = document.getElementById("nav-menu");

if (hamburger && navMenu) {
    hamburger.addEventListener("click", () => {
        navMenu.classList.toggle("active");
        hamburger.classList.toggle("active");
    });

    document.querySelectorAll(".nav-menu a").forEach(link => {
        link.addEventListener("click", () => {
            navMenu.classList.remove("active");
            hamburger.classList.remove("active");
        });
    });
}
