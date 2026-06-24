function showDay(dayId, element) {
  // Ocultar todas las secciones
  const allSections = document.querySelectorAll(".day-section");
  allSections.forEach((section) => {
    section.classList.remove("active");
  });

  // Mostrar la sección seleccionada
  const selectedSection = document.getElementById(dayId);
  selectedSection.classList.add("active");

  // Actualizar tabs activos
  const allTabs = document.querySelectorAll(".day-tab");
  allTabs.forEach((tab) => {
    tab.classList.remove("active");
  });

  element.classList.add("active");

  // Scroll suave hacia arriba
  window.scrollTo({
    top: document.querySelector(".days-nav").offsetTop - 100,
    behavior: "smooth",
  });
}

// Efecto de aparición en scroll
const observeElements = () => {
  const elements = document.querySelectorAll(
    ".paso-card, .punto-card, .day-header, .day-description"
  );

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.style.opacity = "1";
          entry.target.style.transform = "translateY(0)";
        }
      });
    },
    {
      threshold: 0.1,
      rootMargin: "0px 0px -50px 0px",
    }
  );

  elements.forEach((element) => {
    element.style.opacity = "0";
    element.style.transform = "translateY(30px)";
    element.style.transition = "all 0.6s ease-out";
    observer.observe(element);
  });
};

// Inicializar efectos cuando la página carga
document.addEventListener("DOMContentLoaded", () => {
  observeElements();

  // Manejar navegación por URL hash
  const hash = window.location.hash.substring(1);
  if (hash) {
    const tab = document.querySelector(`[onclick*="${hash}"]`);
    if (tab) {
      showDay(hash, tab);
    }
  }
});

// Lazy loading mejorado para imágenes
const lazyImages = document.querySelectorAll('img[loading="lazy"]');
if ("IntersectionObserver" in window) {
  const imageObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const img = entry.target;
        img.src = img.src;
        img.classList.remove("lazy");
        imageObserver.unobserve(img);
      }
    });
  });

  lazyImages.forEach((img) => {
    imageObserver.observe(img);
  });
}

// Efecto de hover mejorado en las cards
document.querySelectorAll(".paso-card").forEach((card) => {
  card.addEventListener("mouseenter", function () {
    this.style.transform = "translateY(-8px) scale(1.02)";
    this.style.boxShadow = "0 20px 50px rgba(0,0,0,0.4)";
  });

  card.addEventListener("mouseleave", function () {
    this.style.transform = "translateY(0) scale(1)";
    this.style.boxShadow = "0 5px 20px rgba(0,0,0,0.2)";
  });
});
// Navbar scroll effect
window.addEventListener("scroll", function () {
  const navbar = document.querySelector(".navbar");
  if (navbar) {
    if (window.scrollY > 50) {
      navbar.classList.add("scrolled");
    } else {
      navbar.classList.remove("scrolled");
    }
  }
});
