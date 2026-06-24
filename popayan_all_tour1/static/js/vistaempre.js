document.addEventListener("DOMContentLoaded", () => {
  // --- Referencias ---
  const deleteModal = document.getElementById("deleteModal");
  const reactivateModal = document.getElementById("reactivateModal");
  const permanentDeleteModal = document.getElementById("permanentDeleteModal");
  const editProfileModal = document.getElementById("editProfileModal");
  const logoutModal = document.getElementById("logoutModal");

  const userIcon = document.getElementById("userIcon");
  const dropdownMenu = document.getElementById("dropdownMenu");
  const editProfileBtn = document.getElementById("editProfileBtn");
  const logoutBtn = document.getElementById("logoutBtn");

  // --- Dropdown Usuario ---
  if (userIcon && dropdownMenu) {
    userIcon.addEventListener("click", (e) => {
      e.stopPropagation();
      const isOpen = dropdownMenu.classList.contains("open");
      document.querySelectorAll(".dropdown.open").forEach(d => d.classList.remove("open"));
      dropdownMenu.classList.toggle("open", !isOpen);
      userIcon.setAttribute("aria-expanded", String(!isOpen));
    });

    // Cerrar dropdown al hacer click fuera
    document.addEventListener("click", (e) => {
      if (!dropdownMenu.contains(e.target) && e.target !== userIcon) {
        dropdownMenu.classList.remove("open");
        userIcon.setAttribute("aria-expanded", "false");
      }
    });
  }

  // --- Abrir modal de Editar Perfil ---
  if (editProfileBtn && editProfileModal) {
    editProfileBtn.addEventListener("click", (e) => {
      e.preventDefault();
      dropdownMenu?.classList.remove("open");
      editProfileModal.style.display = "block";
    });
  }

  // --- Abrir modal de Cerrar Sesión ---
  if (logoutBtn && logoutModal) {
    logoutBtn.addEventListener("click", (e) => {
      e.preventDefault();
      dropdownMenu?.classList.remove("open");
      logoutModal.style.display = "block";
    });
  }

  // --- Cerrar modales por botón X ---
  document.querySelectorAll(".modal .close").forEach(btn => {
    btn.addEventListener("click", () => {
      const which = btn.getAttribute("data-close");
      if (which === "editProfile") editProfileModal.style.display = "none";
      if (which === "logout") logoutModal.style.display = "none";
      if (which === "delete") deleteModal.style.display = "none";
      if (which === "reactivate") reactivateModal.style.display = "none";
      if (which === "permanent") permanentDeleteModal.style.display = "none";
    });
  });

  // --- Botones de cancelar ---
  const cancelEditProfile = document.getElementById("cancelEditProfile");
  if (cancelEditProfile && editProfileModal) {
    cancelEditProfile.addEventListener("click", () => {
      editProfileModal.style.display = "none";
    });
  }

  const cancelLogout = document.getElementById("cancelLogout");
  if (cancelLogout && logoutModal) {
    cancelLogout.addEventListener("click", () => {
      logoutModal.style.display = "none";
    });
  }

  const cancelDelete = document.getElementById("cancelDelete");
  if (cancelDelete && deleteModal) {
    cancelDelete.addEventListener("click", () => {
      deleteModal.style.display = "none";
    });
  }

  const cancelReactivate = document.getElementById("cancelReactivate");
  if (cancelReactivate && reactivateModal) {
    cancelReactivate.addEventListener("click", () => {
      reactivateModal.style.display = "none";
    });
  }

  const cancelPermanentDelete = document.getElementById("cancelPermanentDelete");
  if (cancelPermanentDelete && permanentDeleteModal) {
    cancelPermanentDelete.addEventListener("click", () => {
      permanentDeleteModal.style.display = "none";
    });
  }

  // --- Cerrar modales al click fuera ---
  window.addEventListener("click", (event) => {
    if (event.target === editProfileModal) editProfileModal.style.display = "none";
    if (event.target === logoutModal) logoutModal.style.display = "none";
    if (event.target === deleteModal) deleteModal.style.display = "none";
    if (event.target === reactivateModal) reactivateModal.style.display = "none";
    if (event.target === permanentDeleteModal) permanentDeleteModal.style.display = "none";
  });

  // --- Abrir modal de desactivación ---
  document.querySelectorAll(".delete-trigger").forEach(btn => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-id");
      const name = btn.getAttribute("data-name");
      const tipo = btn.getAttribute("data-tipo");
      
      const nameSpan = document.getElementById("hotelName");
      const deleteForm = document.getElementById("deleteForm");
      
      if (nameSpan) nameSpan.textContent = name;
      if (deleteForm) {
        deleteForm.action = `/empresario/eliminar/${tipo}/${id}/`;
      }
      if (deleteModal) deleteModal.style.display = "block";
    });
  });

  // --- Abrir modal de reactivación ---
  document.querySelectorAll(".reactivate-trigger").forEach(btn => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-id");
      const name = btn.getAttribute("data-name");
      const tipo = btn.getAttribute("data-tipo");
      
      const nameSpan = document.getElementById("reactivateName");
      const reactivateForm = document.getElementById("reactivateForm");
      
      if (nameSpan) nameSpan.textContent = name;
      if (reactivateForm) {
        reactivateForm.action = `/empresario/reactivar/${tipo}/${id}/`;
      }
      if (reactivateModal) reactivateModal.style.display = "block";
    });
  });

  // --- Abrir modal de eliminación PERMANENTE ---
  document.querySelectorAll(".permanent-delete-trigger").forEach(btn => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-id");
      const name = btn.getAttribute("data-name");
      const tipo = btn.getAttribute("data-tipo");
      
      const nameSpan = document.getElementById("permanentDeleteName");
      const permanentForm = document.getElementById("permanentDeleteForm");
      
      if (nameSpan) nameSpan.textContent = name;
      if (permanentForm) {
        permanentForm.action = `/empresario/eliminar-permanente/${tipo}/${id}/`;
      }
      if (permanentDeleteModal) permanentDeleteModal.style.display = "block";
    });
  });
});