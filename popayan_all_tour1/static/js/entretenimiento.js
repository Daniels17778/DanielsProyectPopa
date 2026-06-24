document.getElementById('hamburger').addEventListener('click', function() {
  document.getElementById('nav-menu').classList.toggle('active');
});

// Cerrar menú al hacer click en un enlace
document.querySelectorAll('.nav-menu a').forEach(link => {
  link.addEventListener('click', function() {
    document.getElementById('nav-menu').classList.remove('active');
  });
});

// Navbar scroll
window.addEventListener('scroll', function() {
  const navbar = document.getElementById('navbar');
  if (window.scrollY > 50) {
    navbar.classList.add('scrolled');
  } else {
    navbar.classList.remove('scrolled');
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
