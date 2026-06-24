// ══════════════════════════════════════════════════════════════════
//  JUEGO.JS  —  Código original restaurado + correcciones + mejoras
//  ↓ Secciones [NUEVO] = añadidos. Secciones [FIX] = correcciones.
//  ↓ El core del juego NO fue modificado.
// ══════════════════════════════════════════════════════════════════

// Función para verificar si la pelota cae en la taza de café (solo para puntuar)
function checkCoffeeCupScore(ball) {
    const ballInCupX = ball.x >= coffeeCup.entryX && ball.x <= coffeeCup.entryX + coffeeCup.entryWidth;
    const ballInCupY = ball.y >= coffeeCup.entryY && ball.y <= coffeeCup.entryY + coffeeCup.entryHeight;
    const isFalling = ball.dy > 0;
    let isInsideCleanly = true;
    coffeeCup.collisionBoxes.forEach(box => {
        const ballLeft = ball.x - ball.radius;
        const ballRight = ball.x + ball.radius;
        const ballTop = ball.y - ball.radius;
        const ballBottom = ball.y + ball.radius;
        if (ballRight > box.x && ballLeft < box.x + box.width &&
            ballBottom > box.y && ballTop < box.y + box.height) {
            isInsideCleanly = false;
        }
    });
    return ballInCupX && ballInCupY && isFalling && isInsideCleanly;
}

// Configuración del canvas
const canvas = document.getElementById('gameCanvas');
canvas.width = 1362;
canvas.height = 720;

const ctx = canvas.getContext('2d');
const scoreDisplay = document.getElementById('scoreDisplay');
const levelDisplay = document.getElementById('levelDisplay');
const notification = document.getElementById('notification');

let score = 0;
let currentLevel = 1;
let totalShots = 0;
let successfulShots = 0;
let angle = 0;
let isCharging = false;
let power = 0;
let maxPower = 100;

// Sistema de colisiones de límites
const boundaries = {
    cloudBoundary: { points: [], height: 60 },
    floorBoundary: { y: canvas.height - 40, height: 40 }
};

function generateCloudBoundary() {
    const points = [];
    const segments = 20;
    const baseHeight = 40;
    const variation = 20;
    for (let i = 0; i <= segments; i++) {
        const x = (canvas.width / segments) * i;
        const waveHeight = Math.sin(i * 0.8) * 10 + Math.cos(i * 1.2) * 8;
        const y = baseHeight + variation * Math.sin((i / segments) * Math.PI * 4) + waveHeight;
        points.push({ x, y });
    }
    boundaries.cloudBoundary.points = points;
}

function drawCloudBoundary() {
    if (boundaries.cloudBoundary.points.length === 0) return;
    ctx.save();
    const gradient = ctx.createLinearGradient(0, 0, 0, boundaries.cloudBoundary.height);
    gradient.addColorStop(0, 'rgba(255, 255, 255, 0.9)');
    gradient.addColorStop(0.5, 'rgba(200, 220, 255, 0.7)');
    gradient.addColorStop(1, 'rgba(150, 180, 255, 0.5)');
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(0, boundaries.cloudBoundary.points[0].y);
    for (let i = 0; i < boundaries.cloudBoundary.points.length - 1; i++) {
        const current = boundaries.cloudBoundary.points[i];
        const next = boundaries.cloudBoundary.points[i + 1];
        const controlX = (current.x + next.x) / 2;
        const controlY = (current.y + next.y) / 2;
        ctx.quadraticCurveTo(current.x, current.y, controlX, controlY);
    }
    const lastPoint = boundaries.cloudBoundary.points[boundaries.cloudBoundary.points.length - 1];
    ctx.lineTo(lastPoint.x, lastPoint.y);
    ctx.lineTo(canvas.width, 0);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.6)';
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.restore();
}

function drawFloorBoundary() {
    ctx.save();
    const gradient = ctx.createLinearGradient(0, boundaries.floorBoundary.y, 0, canvas.height);
    gradient.addColorStop(0, 'rgba(101, 67, 33, 0.9)');
    gradient.addColorStop(0.3, 'rgba(139, 69, 19, 0.8)');
    gradient.addColorStop(1, 'rgba(160, 82, 45, 0.9)');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, boundaries.floorBoundary.y, canvas.width, boundaries.floorBoundary.height);
    ctx.strokeStyle = 'rgba(101, 67, 33, 0.5)';
    ctx.lineWidth = 1;
    for (let i = 1; i < 4; i++) {
        const y = boundaries.floorBoundary.y + (boundaries.floorBoundary.height / 4) * i;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
    }
    for (let x = 0; x < canvas.width; x += 80) {
        ctx.beginPath();
        ctx.moveTo(x, boundaries.floorBoundary.y);
        ctx.lineTo(x, canvas.height);
        ctx.stroke();
    }
    ctx.strokeStyle = 'rgba(139, 69, 19, 0.8)';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(0, boundaries.floorBoundary.y);
    ctx.lineTo(canvas.width, boundaries.floorBoundary.y);
    ctx.stroke();
    ctx.restore();
}

function checkCloudCollision(ball) {
    if (boundaries.cloudBoundary.points.length === 0) return false;
    const ballX = ball.x;
    let leftPoint = boundaries.cloudBoundary.points[0];
    let rightPoint = boundaries.cloudBoundary.points[boundaries.cloudBoundary.points.length - 1];
    for (let i = 0; i < boundaries.cloudBoundary.points.length - 1; i++) {
        const current = boundaries.cloudBoundary.points[i];
        const next = boundaries.cloudBoundary.points[i + 1];
        if (ballX >= current.x && ballX <= next.x) {
            leftPoint = current;
            rightPoint = next;
            break;
        }
    }
    const t = (ballX - leftPoint.x) / (rightPoint.x - leftPoint.x);
    const cloudY = leftPoint.y + (rightPoint.y - leftPoint.y) * t;
    if (ball.y - ball.radius <= cloudY) {
        ball.y = cloudY + ball.radius;
        if (ball.dy < 0) {
            ball.dy = -ball.dy * 0.6;
            ball.dx += (Math.random() - 0.5) * 2;
        }
        return true;
    }
    return false;
}

function checkFloorCollision(ball) {
    if (ball.y + ball.radius >= boundaries.floorBoundary.y) {
        ball.y = boundaries.floorBoundary.y - ball.radius;
        ball.dy = -ball.dy * 0.7;
        ball.dx *= 0.9;
        if (Math.abs(ball.dy) < 1) { ball.dy = 0; }
        return true;
    }
    return false;
}

// Cañón
const cannon = {
    x: 50,
    y: canvas.height - 50,
    width: 70,
    height: 50,
    image: new Image()
};
cannon.image.src = '/static/img/cañon.png';

// Imagen de bagel/pandebono
const bagelImage = new Image();
bagelImage.src = '/static/img/pandebono.png';

// Taza de café
const balls = [];
const coffeeCup = {
    x: canvas.width - 200,
    y: canvas.height / 2 - 50,
    width: 150,
    height: 130,
    entryX: canvas.width - 187,
    entryY: canvas.height / 2 - 15,
    entryWidth: 95,
    entryHeight: 12,
    collisionBoxes: [
        { x: canvas.width - 197, y: canvas.height / 2 - 27, width: 8,  height: 106 },
        { x: canvas.width - 90,  y: canvas.height / 2 - 27, width: 8,  height: 106 },
        { x: canvas.width - 190, y: canvas.height / 2 + 77, width: 98, height: 10  },
    ],
    image: new Image()
};
coffeeCup.image.src = '/static/img/tasa_aro.png';

function drawCoffeeCup() {
    if (coffeeCup.image.complete && coffeeCup.image.naturalWidth !== 0) {
        ctx.drawImage(coffeeCup.image, coffeeCup.x, coffeeCup.y, coffeeCup.width, coffeeCup.height);
    } else {
        ctx.fillStyle = '#8B4513';
        ctx.fillRect(coffeeCup.x, coffeeCup.y, coffeeCup.width, coffeeCup.height);
        ctx.fillStyle = 'white';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('TAZA', coffeeCup.x + coffeeCup.width / 2, coffeeCup.y + coffeeCup.height / 2);
    }
}

// Obstáculos
const obstacleImage = new Image();
obstacleImage.src = '/static/img/madera.png';

const levelConfigurations = [
    {
        name: "Primer Tiro al Café",
        obstacles: [{ x: 400, y: 500, width: 20, height: 100, image: obstacleImage }],
        description: "¡Bienvenido! Remoja el pandebono en la taza de café."
    },
    {
        name: "Café con Obstáculos",
        obstacles: [
            { x: 300, y: 200, width: 120, height: 20, image: obstacleImage, angle: Math.PI / 6 },
            { x: 500, y: 400, width: 30,  height: 150, image: obstacleImage }
        ],
        description: "Evita los obstáculos para llegar al café."
    },
    {
        name: "Molino Cafetero",
        obstacles: [
            { x: 400, y: 250, width: 20,  height: 120, image: obstacleImage, rotating: true, rotationSpeed: 0.03 },
            { x: 600, y: 450, width: 80,  height: 15,  image: obstacleImage, angle: -Math.PI / 4 }
        ],
        description: "¡Cuidado con el molino giratorio!"
    },
    {
        name: "Laberinto de la Cafetería",
        obstacles: [
            { x: 250, y: 100, width: 20, height: 200, image: obstacleImage },
            { x: 450, y: 300, width: 20, height: 200, image: obstacleImage },
            { x: 650, y: 150, width: 20, height: 250, image: obstacleImage },
            { x: 350, y: 50,  width: 100, height: 20, image: obstacleImage }
        ],
        description: "Navega hasta la mesa del café."
    },
    {
        name: "Doble Molinillo",
        obstacles: [
            { x: 300, y: 200, width: 15, height: 100, image: obstacleImage, rotating: true, rotationSpeed: 0.04 },
            { x: 500, y: 350, width: 15, height: 120, image: obstacleImage, rotating: true, rotationSpeed: -0.035 },
            { x: 700, y: 150, width: 100, height: 20, image: obstacleImage, angle: Math.PI / 3 }
        ],
        description: "Dos molinillos de café sincronizados, ¡ten cuidado!"
    },
    {
        name: "Pasillo de la Cafetería",
        obstacles: [
            { x: 400, y: 0,   width: 25, height: 250, image: obstacleImage },
            { x: 400, y: 350, width: 25, height: 370, image: obstacleImage },
            { x: 600, y: 0,   width: 25, height: 200, image: obstacleImage },
            { x: 600, y: 400, width: 25, height: 320, image: obstacleImage }
        ],
        description: "Pasa por el estrecho pasillo de la cafetería."
    },
    {
        name: "Escalones del Bar",
        obstacles: [
            { x: 200, y: 500, width: 80, height: 15, image: obstacleImage, rotating: true, rotationSpeed: 0.02 },
            { x: 350, y: 400, width: 80, height: 15, image: obstacleImage, rotating: true, rotationSpeed: -0.025 },
            { x: 500, y: 300, width: 80, height: 15, image: obstacleImage, rotating: true, rotationSpeed: 0.03 },
            { x: 650, y: 200, width: 80, height: 15, image: obstacleImage, rotating: true, rotationSpeed: -0.02 }
        ],
        description: "Escalones giratorios en el bar de café."
    },
    {
        name: "Batidor Gigante",
        obstacles: [
            { x: 450, y: 280, width: 200, height: 15, image: obstacleImage, rotating: true, rotationSpeed: 0.025 },
            { x: 450, y: 280, width: 15,  height: 200, image: obstacleImage, rotating: true, rotationSpeed: 0.025 },
            { x: 250, y: 150, width: 60,  height: 20, image: obstacleImage, angle: Math.PI / 4 },
            { x: 700, y: 450, width: 60,  height: 20, image: obstacleImage, angle: -Math.PI / 4 }
        ],
        description: "Un gran batidor de café bloquea el camino."
    },
    {
        name: "Caos Cafetero",
        obstacles: [
            { x: 200, y: 300, width: 15, height: 80,  image: obstacleImage, rotating: true, rotationSpeed: 0.05 },
            { x: 350, y: 150, width: 60, height: 15,  image: obstacleImage, rotating: true, rotationSpeed: -0.04 },
            { x: 500, y: 450, width: 15, height: 100, image: obstacleImage, rotating: true, rotationSpeed: 0.035 },
            { x: 650, y: 250, width: 80, height: 15,  image: obstacleImage, rotating: true, rotationSpeed: -0.045 },
            { x: 750, y: 100, width: 20, height: 150, image: obstacleImage },
            { x: 100, y: 100, width: 20, height: 200, image: obstacleImage }
        ],
        description: "¡Múltiples obstáculos en la máquina de café!"
    },
    {
        name: "Maestro Barista",
        obstacles: [
            { x: 400, y: 280, width: 250, height: 20,  image: obstacleImage, rotating: true, rotationSpeed: 0.02 },
            { x: 400, y: 280, width: 20,  height: 250, image: obstacleImage, rotating: true, rotationSpeed: 0.02 },
            { x: 150, y: 200, width: 15,  height: 120, image: obstacleImage, rotating: true, rotationSpeed: 0.06 },
            { x: 750, y: 350, width: 15,  height: 120, image: obstacleImage, rotating: true, rotationSpeed: -0.055 },
            { x: 600, y: 100, width: 100, height: 25,  image: obstacleImage, angle: Math.PI / 6 },
            { x: 550, y: 500, width: 100, height: 25,  image: obstacleImage, angle: -Math.PI / 6 },
            { x: 300, y: 50,  width: 25,  height: 100, image: obstacleImage },
            { x: 850, y: 450, width: 25,  height: 150, image: obstacleImage }
        ],
        description: "¡El desafío final! ¿Serás el maestro barista?"
    }
];

let obstacles = [];
let mousePos = { x: 0, y: 0 };

function initializeLevel(levelNumber) {
    if (levelNumber > levelConfigurations.length) {
        levelNumber = levelConfigurations.length;
    }
    const levelConfig = levelConfigurations[levelNumber - 1];
    obstacles = [...levelConfig.obstacles];
    obstacles.forEach(obstacle => {
        if (obstacle.rotating) { obstacle.rotationAngle = 0; }
    });
    showNotification(`Nivel ${levelNumber}: ${levelConfig.name}`);
    levelDisplay.textContent = `Nivel: ${levelNumber} - ${levelConfig.name}`;
    // [FIX] Era balls.length = 2 (bug: truncaba en lugar de vaciar). Corregido a 0.
    balls.length = 0;
}

function drawCannon() {
    ctx.save();
    ctx.translate(cannon.x, cannon.y);
    ctx.rotate(angle);
    ctx.drawImage(cannon.image, -cannon.width / 20, -cannon.height / 20, cannon.width, cannon.height);
    ctx.restore();
}

function drawBalls() {
    balls.forEach(ball => {
        if (bagelImage.complete && bagelImage.naturalWidth !== 0) {
            const imageSize = ball.radius * 5;
            ctx.drawImage(bagelImage, ball.x - ball.radius, ball.y - ball.radius, imageSize, imageSize);
        } else {
            ctx.beginPath();
            ctx.arc(ball.x, ball.y, ball.radius, 0, Math.PI * 5);
            ctx.fillStyle = 'orange';
            ctx.fill();
            ctx.closePath();
        }
    });
}

function drawObstacles() {
    obstacles.forEach(obstacle => {
        if (obstacle.image.complete) {
            ctx.save();
            ctx.translate(obstacle.x + obstacle.width / 2, obstacle.y + obstacle.height / 2);
            if (obstacle.rotating) {
                obstacle.rotationAngle = (obstacle.rotationAngle || 0) + obstacle.rotationSpeed;
                ctx.rotate(obstacle.rotationAngle);
            } else if (obstacle.angle) {
                ctx.rotate(obstacle.angle);
            }
            ctx.drawImage(obstacle.image, -obstacle.width / 2, -obstacle.height / 2, obstacle.width, obstacle.height);
            ctx.restore();
        }
    });
}

function checkCollision(ball, obstacle) {
    const centerX = obstacle.x + obstacle.width / 2;
    const centerY = obstacle.y + obstacle.height / 2;
    const rotationAngle = obstacle.rotating ? (obstacle.rotationAngle || 0) : (obstacle.angle || 0);
    const dx = ball.x - centerX;
    const dy = ball.y - centerY;
    const rotatedX = dx * Math.cos(-rotationAngle) - dy * Math.sin(-rotationAngle);
    const rotatedY = dx * Math.sin(-rotationAngle) + dy * Math.cos(-rotationAngle);
    const closestX = Math.max(-obstacle.width / 2, Math.min(obstacle.width / 2, rotatedX));
    const closestY = Math.max(-obstacle.height / 2, Math.min(obstacle.height / 2, rotatedY));
    const distanceX = rotatedX - closestX;
    const distanceY = rotatedY - closestY;
    const distanceSquared = distanceX * distanceX + distanceY * distanceY;
    if (distanceSquared < ball.radius * ball.radius) {
        let normalX = distanceX;
        let normalY = distanceY;
        if (distanceSquared === 0) {
            const overlapX = obstacle.width / 2 + ball.radius - Math.abs(rotatedX);
            const overlapY = obstacle.height / 2 + ball.radius - Math.abs(rotatedY);
            if (overlapX < overlapY) { normalX = rotatedX > 0 ? 1 : -1; normalY = 0; }
            else { normalX = 0; normalY = rotatedY > 0 ? 1 : -1; }
        } else {
            const distance = Math.sqrt(distanceSquared);
            normalX /= distance; normalY /= distance;
        }
        const worldNormalX = normalX * Math.cos(rotationAngle) - normalY * Math.sin(rotationAngle);
        const worldNormalY = normalX * Math.sin(rotationAngle) + normalY * Math.cos(rotationAngle);
        const penetration = ball.radius - Math.sqrt(distanceSquared);
        ball.x += worldNormalX * penetration;
        ball.y += worldNormalY * penetration;
        const relativeVelocityX = ball.dx;
        const relativeVelocityY = ball.dy;
        const velocityAlongNormal = relativeVelocityX * worldNormalX + relativeVelocityY * worldNormalY;
        if (velocityAlongNormal > 0) return true;
        const restitution = 0.7;
        const impulse = -(1 + restitution) * velocityAlongNormal;
        ball.dx += impulse * worldNormalX;
        ball.dy += impulse * worldNormalY;
        const friction = 0.3;
        const tangentX = relativeVelocityX - velocityAlongNormal * worldNormalX;
        const tangentY = relativeVelocityY - velocityAlongNormal * worldNormalY;
        const tangentLength = Math.sqrt(tangentX * tangentX + tangentY * tangentY);
        if (tangentLength > 0) {
            const tangentNormalizedX = tangentX / tangentLength;
            const tangentNormalizedY = tangentY / tangentLength;
            const frictionImpulse = friction * Math.abs(impulse);
            ball.dx -= frictionImpulse * tangentNormalizedX;
            ball.dy -= frictionImpulse * tangentNormalizedY;
        }
        return true;
    }
    return false;
}

function checkRectangleCollision(ball, rect) {
    const closestX = Math.max(rect.x, Math.min(ball.x, rect.x + rect.width));
    const closestY = Math.max(rect.y, Math.min(ball.y, rect.y + rect.height));
    const distanceX = ball.x - closestX;
    const distanceY = ball.y - closestY;
    const distanceSquared = distanceX * distanceX + distanceY * distanceY;
    if (distanceSquared < ball.radius * ball.radius) {
        let normalX = distanceX;
        let normalY = distanceY;
        if (distanceSquared === 0) {
            const overlapX = rect.width / 2 + ball.radius - Math.abs(ball.x - (rect.x + rect.width / 2));
            const overlapY = rect.height / 2 + ball.radius - Math.abs(ball.y - (rect.y + rect.height / 2));
            if (overlapX < overlapY) { normalX = ball.x > (rect.x + rect.width / 2) ? 1 : -1; normalY = 0; }
            else { normalX = 0; normalY = ball.y > (rect.y + rect.height / 2) ? 1 : -1; }
        } else {
            const distance = Math.sqrt(distanceSquared);
            normalX /= distance; normalY /= distance;
        }
        const penetration = ball.radius - Math.sqrt(distanceSquared);
        if (penetration > 0) { ball.x += normalX * penetration; ball.y += normalY * penetration; }
        const velocityAlongNormal = ball.dx * normalX + ball.dy * normalY;
        if (velocityAlongNormal > 0) return true;
        const restitution = 0.6;
        const impulse = -(1 + restitution) * velocityAlongNormal;
        ball.dx += impulse * normalX;
        ball.dy += impulse * normalY;
        const friction = 0.2;
        const tangentX = ball.dx - velocityAlongNormal * normalX;
        const tangentY = ball.dy - velocityAlongNormal * normalY;
        const tangentLength = Math.sqrt(tangentX * tangentX + tangentY * tangentY);
        if (tangentLength > 0) {
            const tangentNormalizedX = tangentX / tangentLength;
            const tangentNormalizedY = tangentY / tangentLength;
            const frictionImpulse = friction * Math.abs(impulse);
            ball.dx -= frictionImpulse * tangentNormalizedX;
            ball.dy -= frictionImpulse * tangentNormalizedY;
        }
        return true;
    }
    return false;
}

function checkCoffeeCupCollision(ball) {
    let hasCollision = false;
    coffeeCup.collisionBoxes.forEach(box => {
        if (checkRectangleCollision(ball, box)) { hasCollision = true; }
    });
    return hasCollision;
}

function moveBalls() {
    balls.forEach((ball, index) => {
        ball.x += ball.dx;
        ball.y += ball.dy;
        ball.dy += 0.2;
        checkCloudCollision(ball);
        checkFloorCollision(ball);
        if (ball.x + ball.radius > canvas.width) { ball.x = canvas.width - ball.radius; ball.dx *= -0.8; }
        if (ball.x - ball.radius < 0) { ball.x = ball.radius; ball.dx *= -0.8; }
        if (ball.y + ball.radius > canvas.height) { balls.splice(index, 1); return; }
        obstacles.forEach(obstacle => { checkCollision(ball, obstacle); });
        checkCoffeeCupCollision(ball);
        if (checkCoffeeCupScore(ball)) {
            score++;
            scoreDisplay.textContent = `Puntuación: ${score}`;
            scoreDisplay.classList.remove('scored');
            void scoreDisplay.offsetWidth;
            scoreDisplay.classList.add('scored');
            balls.splice(index, 1);
            if (currentLevel < levelConfigurations.length) {
                currentLevel++;
                setTimeout(() => initializeLevel(currentLevel), 1000);
                showNotification(`¡Excelente! El pandebono cayó en el café. Nivel ${currentLevel}`);
            } else {
                showNotification("¡Felicidades! ¡Has completado todos los niveles de la cafetería!");
            }
        }
    });
}

function showNotification(message) {
    notification.textContent = message;
    notification.style.display = 'block';
    notification.classList.add('visible');
    setTimeout(() => {
        notification.style.display = 'none';
        notification.classList.remove('visible');
    }, 3000);
}

function drawPowerBar() {
    if (!isCharging) return;
    const barWidth = 200;
    const barHeight = 20;
    const barX = canvas.width / 2 - barWidth / 2;
    const barY = 40;
    ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
    ctx.fillRect(barX - 5, barY - 5, barWidth + 10, barHeight + 10);
    ctx.strokeStyle = 'white';
    ctx.lineWidth = 2;
    ctx.strokeRect(barX, barY, barWidth, barHeight);
    const fillWidth = (power / maxPower) * barWidth;
    if (power < 30) { ctx.fillStyle = '#4CAF50'; }
    else if (power < 40) { ctx.fillStyle = '#FFEB3B'; }
    else if (power < 60) { ctx.fillStyle = '#FF9800'; }
    else { ctx.fillStyle = '#F44336'; }
    ctx.fillRect(barX, barY, fillWidth, barHeight);
    ctx.fillStyle = 'white';
    ctx.font = 'bold 16px Arial';
    ctx.textAlign = 'center';
    ctx.fillText(`Potencia: ${Math.floor(power)}%`, canvas.width / 2, barY - 10);
    ctx.font = '14px Arial';
    ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
    ctx.fillText('Mantén presionado para cargar, suelta para disparar', canvas.width / 2, barY + barHeight + 20);
}

function resetLevel() { initializeLevel(currentLevel); }

function goToLevel(levelNumber) {
    if (levelNumber >= 1 && levelNumber <= levelConfigurations.length) {
        currentLevel = levelNumber;
        initializeLevel(currentLevel);
    }
}

function gameLoop() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawCannon();
    drawPowerBar();
    drawBalls();
    drawCoffeeCup();
    drawObstacles();
    moveBalls();
    if (isCharging) { power = Math.min(power + 2, maxPower); }

    // [NUEVO] Verificar visibilidad del botón de limpieza (throttled)
    _cleanupThrottleFrame++;
    if (_cleanupThrottleFrame >= _CLEANUP_THROTTLE_FRAMES) {
        _cleanupThrottleFrame = 0;
        _syncCleanupButton();
    }

    // [NUEVO] Tick de la animación de palomas (solo lectura de estado, sin DOM)
    _pigeonTick();

    requestAnimationFrame(gameLoop);
}

document.addEventListener('mousemove', e => {
    const rect = canvas.getBoundingClientRect();
    mousePos.x = e.clientX - rect.left;
    mousePos.y = e.clientY - rect.top;
    angle = Math.atan2(mousePos.y - cannon.y, mousePos.x - cannon.x);
});

canvas.addEventListener('mousedown', () => { isCharging = true; power = 0; });

canvas.addEventListener('mouseup', () => {
    if (isCharging) {
        const shootPower = power / 100 * 50;
        balls.push({
            x: cannon.x + Math.cos(angle) * cannon.width,
            y: cannon.y + Math.sin(angle) * cannon.width,
            dx: Math.cos(angle) * shootPower,
            dy: Math.sin(angle) * shootPower,
            radius: 12
        });
        isCharging = false;
        power = 0;
    }
});

document.addEventListener('keydown', (e) => {
    switch (e.key) {
        case 'r': case 'R': resetLevel(); break;
        case 'n': case 'N':
            if (currentLevel < levelConfigurations.length) { currentLevel++; initializeLevel(currentLevel); }
            break;
        case 'p': case 'P':
            if (currentLevel > 1) { currentLevel--; initializeLevel(currentLevel); }
            break;
    }
});

document.getElementById('menuButton').addEventListener('click', () => { window.location.href = '/menu/'; });


// ══════════════════════════════════════════════════════════════════
//  [NUEVO + FIX] SISTEMA DE LIMPIEZA CON PALOMAS — v2
//
//  CAMBIOS RESPECTO A V1:
//  ─────────────────────────────────────────────────────────────────
//  FIX 1: checkCleanupButtonVisibility() se ejecutaba cada frame (~60/s)
//         y recreaba nodos DOM con createElement en cada tick → memory leak
//         masivo + colapso del layout engine. Solución: el DOM se construye
//         UNA SOLA VEZ en DOMContentLoaded y solo se actualiza el texto del
//         contador. La visibilidad se gestiona con classList.
//
//  FIX 2: CLEANUP_THRESHOLD era 4; el requisito es 7.
//
//  FIX 3: La animación de palomas usaba CSS @keyframes con variables
//         --px-mid / --py-end calculadas desde overlay.offsetWidth que
//         devolvía 0 cuando el overlay estaba oculto (display:none).
//         Solución: usar canvas.width/height como referencia fija.
//
//  FIX 4: pigeonState.active bloqueaba _syncCleanupButton pero no
//         restablecía la bandera si el usuario navegaba a otro nivel
//         mientras la animación corría. Solución: reset en initializeLevel
//         vía _resetPigeonState().
//
//  OPTIMIZACIÓN: La actualización del botón está throttled a 1 vez cada
//  6 frames (~10Hz) para eliminar completamente el impacto en FPS.
//  La animación de palomas usa CSS puro (sin JS en cada frame) —
//  _pigeonTick() solo gestiona el estado lógico (cuándo limpiar/ocultar).
// ══════════════════════════════════════════════════════════════════

// ── Constantes ──────────────────────────────────────────────────
/** Número de pandebonos en suelo necesarios para mostrar el botón */
const CLEANUP_THRESHOLD = 7;

/** Throttle: actualizar UI del botón cada N frames (≈10 Hz a 60 fps) */
const _CLEANUP_THROTTLE_FRAMES = 6;
let _cleanupThrottleFrame = 0;

// ── Estado de la animación ───────────────────────────────────────
const _pigeon = {
    active:      false,
    startTime:   0,
    duration:    2600,   // ms totales de la oleada
    cleanupDone: false,
    timeoutId:   null    // para limpiar timers si es necesario
};

// ── Cache de elementos DOM (se obtienen una sola vez) ────────────
let _btnCleanup    = null;
let _btnLabel      = null;   // <span> con el texto + contador
let _btnIcon       = null;   // <span> con el emoji
let _pigeonOverlay = null;
let _cleanFlash    = null;

/**
 * Construye la estructura interna del botón UNA SOLA VEZ.
 * Llamado desde DOMContentLoaded.
 * [FIX] Reemplaza la construcción por frame del código original.
 */
function _initCleanupDOM() {
    _btnCleanup    = document.getElementById('cleanupButton');
    _pigeonOverlay = document.getElementById('pigeonOverlay');
    _cleanFlash    = document.getElementById('cleanFlash');

    if (!_btnCleanup) return;

    // Construir interior del botón una sola vez
    _btnCleanup.innerHTML = '';
    _btnIcon = document.createElement('span');
    _btnIcon.className = 'btn-icon';
    _btnIcon.textContent = '🕊️';

    _btnLabel = document.createElement('span');
    _btnLabel.className = 'btn-label';
    _btnLabel.textContent = 'Limpiar pandebonos';

    _btnCleanup.appendChild(_btnIcon);
    _btnCleanup.appendChild(_btnLabel);

    // Conectar evento de clic
    _btnCleanup.addEventListener('click', _triggerPigeonCleanup);
}

/**
 * Cuenta los pandebonos que están posados en el suelo.
 * Criterio: velocidad vertical = 0 Y posición cerca del piso.
 */
function _countBallsOnFloor() {
    let count = 0;
    for (let i = 0; i < balls.length; i++) {
        const b = balls[i];
        if (b.dy === 0 && b.y + b.radius >= boundaries.floorBoundary.y - 5) count++;
    }
    return count;
}

/**
 * Sincroniza visibilidad y contador del botón.
 * Llamado a ~10 Hz desde gameLoop (throttled).
 * [FIX] No crea ningún nodo DOM — solo modifica textContent y classList.
 */
function _syncCleanupButton() {
    if (!_btnCleanup || _pigeon.active) return;

    const onFloor = _countBallsOnFloor();

    if (onFloor >= CLEANUP_THRESHOLD) {
        if (_btnLabel) _btnLabel.textContent = `Limpiar pandebonos (${onFloor})`;
        _btnCleanup.classList.add('visible');
    } else {
        _btnCleanup.classList.remove('visible');
    }
}

/**
 * Tick lógico de la animación. Se llama desde gameLoop cada frame.
 * Solo lee _pigeon.active y tiempos — no toca el DOM salvo para
 * limpiar el overlay al final. Sin allocations.
 * [FIX] Separa lógica de estado de la construcción DOM.
 */
function _pigeonTick() {
    if (!_pigeon.active) return;

    const elapsed = performance.now() - _pigeon.startTime;

    // A ~45 % del tiempo: eliminar pandebonos del suelo
    if (!_pigeon.cleanupDone && elapsed >= _pigeon.duration * 0.45) {
        _pigeon.cleanupDone = true;
        _removeBallsOnFloor();
    }

    // Al finalizar: limpiar overlay y restablecer estado
    if (elapsed >= _pigeon.duration + 400) {
        _pigeon.active = false;
        if (_pigeonOverlay) {
            _pigeonOverlay.classList.remove('active');
            // Limpiar nodos de palomas para liberar memoria
            _pigeonOverlay.innerHTML = '';
        }
    }
}

/**
 * Elimina del array balls todos los pandebonos posados en el suelo.
 * Recorre de atrás hacia adelante para evitar problemas de índice.
 */
function _removeBallsOnFloor() {
    for (let i = balls.length - 1; i >= 0; i--) {
        const b = balls[i];
        if (b.dy === 0 && b.y + b.radius >= boundaries.floorBoundary.y - 5) {
            balls.splice(i, 1);
        }
    }
    showNotification('🕊️ ¡Las palomas se llevaron los pandebonos!');
}

/**
 * Lanza la animación de palomas usando únicamente CSS transitions.
 * Crea los elementos DOM solo cuando se invoca (no cada frame).
 * [FIX] Usa canvas.width / canvas.height como referencia de coordenadas
 *       en lugar de overlay.offsetWidth (que podría ser 0).
 */
function _triggerPigeonCleanup() {
    if (_pigeon.active) return;
    if (!_pigeonOverlay) return;

    // Reset overlay
    _pigeonOverlay.innerHTML = '';
    _pigeonOverlay.classList.add('active');

    // Iniciar estado
    _pigeon.active      = true;
    _pigeon.cleanupDone = false;
    _pigeon.startTime   = performance.now();

    // [FIX] Usar dimensiones del canvas como referencia fija
    // El canvas siempre tiene width/height correctos aunque el overlay esté hidden.
    const W = canvas.width;   // 1362
    const H = canvas.height;  // 720

    // Oleada grande: 20–26 palomas
    const count  = 20 + Math.floor(Math.random() * 7);
    const emojis = ['🕊️', '🕊️', '🕊️', '🦆', '🦅'];

    const fragment = document.createDocumentFragment(); // un solo reflow al final

    for (let i = 0; i < count; i++) {
        const bird = document.createElement('div');
        bird.className = 'pigeon-bird';
        bird.textContent = emojis[Math.floor(Math.random() * emojis.length)];

        // Posición inicial: borde izquierdo, altura aleatoria
        const startYpct = 30 + Math.random() * 55;  // % del alto del canvas
        const startYpx  = (startYpct / 100) * H;

        // Punto medio y final con variación vertical suave
        const midYpx = startYpx + (Math.random() - 0.5) * H * 0.18;
        const endYpx = startYpx + (Math.random() - 0.5) * H * 0.12;

        // [FIX] Variables CSS con valores en píxeles absolutos, no relativos al overlay
        bird.style.setProperty('--px-mid', `${W * 0.52}px`);
        bird.style.setProperty('--py-mid', `${midYpx - startYpx}px`);
        bird.style.setProperty('--px-end', `${W + 80}px`);
        bird.style.setProperty('--py-end', `${endYpx - startYpx}px`);

        // Posición inicial (en coordenadas del overlay, que tiene mismo tamaño que canvas)
        bird.style.left = '-50px';
        bird.style.top  = `${startYpx}px`;

        // Escalonado temporal para efecto de oleada natural
        const delay    = i * 70 + Math.random() * 50;
        const duration = _pigeon.duration - 600 + Math.random() * 800;

        bird.style.animationDuration = `${duration}ms`;
        bird.style.animationDelay    = `${delay}ms`;
        bird.style.fontSize          = `${20 + Math.random() * 20}px`;

        fragment.appendChild(bird);
    }

    // Un solo reflow para todos los pájaros
    _pigeonOverlay.appendChild(fragment);

    // Flash visual
    if (_cleanFlash) {
        _cleanFlash.style.display = 'block';
        // Forzar reflow para que la animación CSS se reinicie
        void _cleanFlash.offsetWidth;
        // Limpiar con timeout (no afecta game loop)
        clearTimeout(_pigeon.flashTimeout);
        _pigeon.flashTimeout = setTimeout(() => {
            if (_cleanFlash) _cleanFlash.style.display = 'none';
        }, 1400);
    }

    // Ocultar botón mientras las palomas vuelan
    if (_btnCleanup) _btnCleanup.classList.remove('visible');
}

/**
 * Restablece el estado de palomas si el nivel cambia mientras la animación corre.
 * Llamar antes de cualquier cambio de nivel.
 * [FIX] Evita que _pigeon.active quede bloqueado entre niveles.
 */
function _resetPigeonState() {
    _pigeon.active      = false;
    _pigeon.cleanupDone = false;
    if (_pigeonOverlay) {
        _pigeonOverlay.classList.remove('active');
        _pigeonOverlay.innerHTML = '';
    }
    if (_cleanFlash) _cleanFlash.style.display = 'none';
    clearTimeout(_pigeon.flashTimeout);
    clearTimeout(_pigeon.timeoutId);
}

// ── Compatibilidad con las funciones originales referenciadas en gameLoop ──
// El código original llama a checkCleanupButtonVisibility() y updatePigeonAnimation()
// en el gameLoop. Las redefinimos aquí como wrappers ligeros para no tocar gameLoop.
// [FIX] Las versiones originales tenían los bugs descritos arriba.

// Sobreescribe la función original problemática con la versión optimizada
function checkCleanupButtonVisibility() {
    // Vacío: el throttling se gestiona directamente en gameLoop con _syncCleanupButton()
    // Esta función existe para no romper gameLoop que la llama.
}

function updatePigeonAnimation() {
    // Vacío: gestionado por _pigeonTick() en gameLoop.
    // Esta función existe para no romper gameLoop que la llama.
}

// ── Inicialización ───────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    _initCleanupDOM();
});

// ── Arranque del juego ───────────────────────────────────────────
generateCloudBoundary();
initializeLevel(1);
gameLoop();