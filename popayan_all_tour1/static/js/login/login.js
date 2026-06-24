
document.querySelector(".see-password").addEventListener("click", function() {
    const passwordInput = document.getElementById("password");
    const icon = this.querySelector("i");

    if (passwordInput.type === "password") {
        passwordInput.type = "text";
        icon.classList.remove("bi-eye-slash");
        icon.classList.add("bi-eye");
    } else {
        passwordInput.type = "password";
        icon.classList.remove("bi-eye");
        icon.classList.add("bi-eye-slash");
    }
});

document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("form");
    const button = document.getElementById("loginBtn");

    form.addEventListener("submit", function () {
        button.disabled = true;
        button.innerText = "Ingresando...";
    });
});