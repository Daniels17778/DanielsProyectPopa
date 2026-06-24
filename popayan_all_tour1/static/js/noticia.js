async function cargarClima() {
    const apiKey = "ff6363700c80de4ed22e43caa2e50681";
    const url = `https://api.openweathermap.org/data/2.5/weather?q=Popayan,CO&appid=${apiKey}&units=metric&lang=es`;

    try {
        const res = await fetch(url);
        const data = await res.json();

        console.log("Respuesta API:", data);

        // Mostrar error si la API falla
        if (!data.weather || !data.main) {
            document.getElementById("weather").innerHTML =
                `Error: ${data.message || "Respuesta inválida de la API"}`;
            return;
        }

        const icono = `https://openweathermap.org/img/wn/${data.weather[0].icon}@2x.png`;

        // =============================
        // FONDOS SEGÚN CLIMA
        // =============================
        const widget = document.getElementById("weather");

        const fondos = {
            clear: "https://images.unsplash.com/photo-1501975558162-0be7b0f4e837?q=80&w=1080&auto=format",
            clouds: "https://images.unsplash.com/photo-1499346030926-9a72daac6c63?q=80&w=1080&auto=format",
            rain: "https://images.unsplash.com/photo-1501594907352-04cda38ebc29?q=80&w=1080&auto=format",
            thunderstorm: "https://images.unsplash.com/photo-1500674425229-f692875b0ab7?q=80&w=1080&auto=format",
            drizzle: "https://images.unsplash.com/photo-1527766833261-b09c3163a791?q=80&w=1080&auto=format",
            snow: "https://images.unsplash.com/photo-1608889175123-99d89bc3ff9b?q=80&w=1080&auto=format",
            mist: "https://images.unsplash.com/photo-1482192596544-9eb780fc7f66?q=80&w=1080&auto=format",
        };

        const clima = data.weather[0].main.toLowerCase();
        console.log("Clima detectado:", clima);

        let backgroundImage = fondos.clear; // valor por defecto

        if (fondos[clima]) {
            backgroundImage = fondos[clima];
        }

        // Aplicar fondo dinámico al widget
        widget.style.backgroundImage = `url('${backgroundImage}')`;

        // =============================
        // HTML del widget
        // =============================
        widget.innerHTML = `
            <div class="weather-status">${data.weather[0].description}</div>
            <div class="weather-icon">
                <img src="${icono}">
            </div>
            <div class="weather-temp">${data.main.temp}°C</div>

            <div class="weather-details">
                <div>
                    <small>Viento</small>
                    <span>${data.wind.speed} km/h</span>
                </div>
                <div>
                    <small>Humedad</small>
                    <span>${data.main.humidity}%</span>
                </div>
            </div>
        `;
    } catch (error) {
        document.getElementById("weather").innerHTML =
            "Error cargando clima: " + error;
    }
}

cargarClima();
