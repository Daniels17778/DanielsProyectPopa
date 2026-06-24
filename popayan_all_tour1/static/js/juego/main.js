// Navbar scroll effect
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

// INICIALIZACION DE VARIABLES
let tarjetasDestapadas = 0;
let tarjeta1 = null;
let tarjeta2 = null;
let primerResultado = null;
let segundoResultado = null;
let movimientos = 0;
let aciertos = 0;
let temporizador = false;
let timer = 60;
let timerIncial = 60;
let tiempoRegresivoId = null;

let nivelActual = 1; // Nivel inicial
let nivelesPasados = 0; // Niveles pasados acumulados

// AUDIO
const winAudio = new Audio('../sounds/win.mp3');
const loseAudio = new Audio('../sounds/lose.mp3');
const clickAudio = new Audio('../sounds/click.mp3');
const rightAudio = new Audio('../sounds/right.mp3');
const wrongAudio = new Audio('../sounds/wrong.mp3');

// APUNTANDO A DOCUMENTO HTML
const mostrarMovimientos = document.getElementById('movimientos');
const mostrarAciertos = document.getElementById('aciertos');
const mostrarTiempo = document.getElementById('t-restante');
const mostrarNiveles = document.getElementById('niveles-pasados');

// CONFIGURACION DE NIVELES
const tiempoPorNivel = {
  1: 60,
  2: 50,
  3: 40,
  4: 30,
  5: 20
};

// GENERACION DE NUMEROS ALEATORIOS
let numeros = [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8];
numeros = shuffleArray(numeros); // Orden aleatorio de números
console.log(numeros);

// Función para mezclar el array
function shuffleArray(arr) {
  return arr.sort(() => Math.random() - 0.5);
}

// Función para contar el tiempo
function contarTiempo() {
  tiempoRegresivoId = setInterval(() => {
    if (timer > 0) {
      timer--;
      mostrarTiempo.innerHTML = `Tiempo: ${timer} segundos`;
    } else {
      clearInterval(tiempoRegresivoId);
      bloquearTarjetas();
      loseAudio.play();
      mostrarTiempo.innerHTML = "¡Tiempo agotado!";
      setTimeout(reiniciarJuego, 3000);
    }
  }, 1000);
}

// Función para bloquear todas las tarjetas
function bloquearTarjetas() {
  for (let i = 0; i <= 15; i++) {
    let tarjetaBloquiada = document.getElementById(i);
    tarjetaBloquiada.innerHTML = `<img src="${rutaImagenes}${numeros[i]}.jpg" alt="">`;
    tarjetaBloquiada.disabled = true;
  }
}

// Función para reiniciar el juego
function reiniciarJuego() {
  clearInterval(tiempoRegresivoId);

  // Configurar el tiempo inicial según el nivel actual
  timer = tiempoPorNivel[nivelActual] || 60;
  timerIncial = timer;

  // Restablecer las variables del juego
  movimientos = 0;
  aciertos = 0;
  tarjetasDestapadas = 0;
  temporizador = false;

  // Actualizar estadísticas y mostrar nivel
  mostrarMovimientos.innerHTML = `Movimientos: ${movimientos}`;
  mostrarAciertos.innerHTML = `Aciertos: ${aciertos}`;
  mostrarTiempo.innerHTML = `Tiempo: ${timer} segundos`;
  mostrarNiveles.innerHTML = `Niveles Pasados: ${nivelesPasados}`;

  // Generar nuevos números y restablecer las tarjetas
  numeros = shuffleArray([1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8]);

  // Reiniciar todas las tarjetas a su estado inicial
  for (let i = 0; i <= 15; i++) {
    let tarjeta = document.getElementById(i);
    tarjeta.disabled = false;
    tarjeta.innerHTML = '';
  }
}

// Función para incrementar el nivel
function incrementarNivel() {
  if (nivelActual < 5) {
    nivelActual++;
    nivelesPasados++;
    mostrarNiveles.innerHTML = `Niveles Pasados: ${nivelesPasados}`;

    // Configuración de tiempo para el siguiente nivel
    timer = tiempoPorNivel[nivelActual];
    setTimeout(reiniciarJuego, 5000);  // Espera 5 segundos antes de iniciar el siguiente nivel
  } else {
    alert("¡Felicidades! Has completado todos los niveles y ganaste tu premio!");
    // Aquí podrías redirigir o mostrar algo especial
  }
}

// Función principal para destapar las tarjetas
function destapar(id) {
  // Evitar que se pueda hacer click en la misma tarjeta dos veces
  const tarjetaClickeada = document.getElementById(id);
  if (tarjetaClickeada.disabled) {
    return;
  }

  if (!temporizador) {
    contarTiempo();
    temporizador = true;
  }

  tarjetasDestapadas++;
  console.log(tarjetasDestapadas);

  if (tarjetasDestapadas === 1) {
    // Mostrar primera imagen
    tarjeta1 = document.getElementById(id);
    primerResultado = numeros[id];
    tarjeta1.innerHTML = `<img src="${rutaImagenes}${primerResultado}.jpg" alt="">`;
    clickAudio.play();
    tarjeta1.disabled = true;
  } else if (tarjetasDestapadas === 2) {
    // Mostrar segunda imagen
    tarjeta2 = document.getElementById(id);
    segundoResultado = numeros[id];
    tarjeta2.innerHTML = `<img src="${rutaImagenes}${segundoResultado}.jpg" alt="">`;
    tarjeta2.disabled = true;

    // Incrementar movimientos
    movimientos++;
    mostrarMovimientos.innerHTML = `Movimientos: ${movimientos}`;

    // Comprobar si las tarjetas coinciden
    if (primerResultado === segundoResultado) {
      tarjetasDestapadas = 0;
      aciertos++;
      mostrarAciertos.innerHTML = `Aciertos: ${aciertos}`;
      rightAudio.play();

      if (aciertos === 8) {
        winAudio.play();
        clearInterval(tiempoRegresivoId);
        mostrarAciertos.innerHTML = `Aciertos: ${aciertos} 🥳️`;
        mostrarTiempo.innerHTML = `Fantástico, solo demoraste ${timerIncial - timer} segundos`;
        mostrarMovimientos.innerHTML = `Movimientos: ${movimientos} 🤭😎`;

        // Incrementar nivel y actualizar
        incrementarNivel();
      }
    } else {
      wrongAudio.play();
      setTimeout(() => {
        tarjeta1.innerHTML = '';
        tarjeta2.innerHTML = '';
        tarjeta1.disabled = false;
        tarjeta2.disabled = false;
        tarjetasDestapadas = 0;
      }, 800);
    }
  }
}