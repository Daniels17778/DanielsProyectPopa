function formatoMinutosSegundos(segundosTotales) {
  const minutos = Math.floor(segundosTotales / 60);
  const segundos = Math.floor(segundosTotales % 60);
  const segundosConCero = segundos < 10 ? `0${segundos}` : segundos;
  return `${minutos}:${segundosConCero}`;
}

export class Juego extends Phaser.Scene {
  constructor() {
    super("Juego");
  }

  preload() {
    // === CARGA DE ASSETS ===
    // estadios
    this.load.image("estadioDia", "/static/assets/stadiumDay.png");
    this.load.image("estadioTarde", "/static/assets/stadiumEvenning.png");
    this.load.image("estadioNoche", "/static/assets/stadiumNigth.png");
    // personajes
    this.load.image("Diablito", "/static/assets/diablito.png");
    this.load.image("Sahumadora", "/static/assets/sahumadora.png");
    this.load.image("Parroco", "/static/assets/parroco.png");
    this.load.image("Sabio Caldas", "/static/assets/sabiocaldas.png");
    this.load.image("Carguero", "/static/assets/carguero.png");
    this.load.image("Chirimia", "/static/assets/chirimia.png");
    // personajes botas
    this.load.image("BotaDiablito", "/static/assets/bota_diablito.png");
    this.load.image("BotaSahumadora", "/static/assets/bota_sahumadora.png");
    this.load.image("BotaParroco", "/static/assets/bota_parroco.png");
    this.load.image("BotaCaldas", "/static/assets/bota_caldas.png");
    this.load.image("BotaCarguero", "/static/assets/bota_carguero.png");
    this.load.image("BotaChirimia", "/static/assets/bota_chirimia.png");
    //jsons botas
    this.load.json("playerOneBootShape", "/static/json/playerOneBootJSON.json");
    this.load.json("playerTwoBootShape", "/static/json/playerTwoBootJSON.json");
    // balón
    this.load.image("ball", "/static/assets/ball.png");
    // teclas
    this.load.image("playerOneKeys", "/static/assets/teclasPlayerOne.png");
    this.load.image("playerTwoKeys", "/static/assets/teclasPlayerTwo.png");
    // logo
    this.load.image("logo", "/static/assets/title.png");
    // sonido
    this.load.image("music", "/static/assets/music.png");
    this.load.image("noMusic", "/static/assets/noMusic.png");
    this.load.image("sound", "/static/assets/sound.png");
    this.load.image("noSound", "/static/assets/noSound.png");
    // botones
    this.load.image("menu", "/static/assets/menu.png");
    this.load.image("pausa", "/static/assets/pausa.png");
    this.load.image("reanudar", "/static/assets/reanudar.png");
    // porterías
    this.load.image("porteriaUno", "/static/assets/frameOne.png");
    this.load.image("porteriaDos", "/static/assets/frameTwo.png");
    // marco
    this.load.image("frame", "/static/assets/frame.png");
    // marcador
    this.load.image("scoreBg", "/static/assets/marcador.png");
    this.load.image("timeBg", "/static/assets/tiempo.png");
    // pasto
    this.load.image("grass", "/static/assets/grass.png");
    //pause overlay
    this.load.image("pauseScreen", "/static/assets/pause_screen.png");
    //game over overlay
    this.load.image("gameOverText", "/static/assets/gameOverText.png");
    this.load.image("gameOverScreen", "/static/assets/gamerOverScreen.png");
  }

  create() {
    this.matter.world.setBounds(0, 0, 1280, 720, 50, true, true, true, true);

    // === TIEMPO ===
    let tiempoRestante = 60;
    let tiempoTexto;

    const clima = this.game.registry.get("climaSelected");
    const playerOne = this.game.registry.get("playerOneSelected");
    const playerTwo = this.game.registry.get("playerTwoSelected");
    const playerOneBoot = this.game.registry.get("playerOneBootS");
    const playerTwoBoot = this.game.registry.get("playerTwoBootS");
    this.stadiums = ["estadioDia", "estadioTarde", "estadioNoche"];
    this.musica = ["music", "noMusic"];
    this.sonido = ["sound", "noSound"];
    this.currentIndexMusic = 0;
    this.currentIndexSound = 0;

    // === FONDO DEL ESTADIO ===
    let background = this.add.image(0, 0, clima).setOrigin(0);
    background.setDisplaySize(1280, 720);
    background.setAlpha(0.9);

    // === SUELO (FÍSICO) ===
    this.grassBg = this.matter.add.image(640, 615, "grass", null, { isStatic: true, label: 'ground' }).setScale(15, 0.06);

    // Barra azul inferior
    const blueBg = this.add.graphics();
    blueBg.fillStyle(0x2357e2, 1);
    blueBg.fillRoundedRect(0, 630, 1280, 90);

    // === TECLAS INFO (UI) ===
    this.teclasPlayerOne = this.add.image(50, 645, "playerOneKeys").setOrigin(0).setScale(0.2);
    this.teclasPlayerTwo = this.add.image(245, 645, "playerTwoKeys").setOrigin(0).setScale(0.2);

    // Líneas decorativas
    const linea = this.add.graphics();
    linea.fillStyle(0xffffff, 0.5);
    linea.fillRect(550, 640, 2, 70);

    const linea1 = this.add.graphics();
    linea1.fillStyle(0xffffff, 0.5);
    linea1.fillRect(745, 640, 2, 70);

    // === LOGOS Y BOTONES (UI) ===
    this.logo = this.add.image(645, 680, "logo").setScale(0.04);

    // === MARCO Y MARCADOR (UI) ===
    this.frame = this.add.image(640, 362, "frame").setScale(1.77, 1.57);

    const scoreboardBg = this.add.graphics();
    scoreboardBg.fillStyle(0x2357e2, 1).fillRoundedRect(400, 50, 545, 50, { tl: 10, tr: 10, bl: 10, br: 10 });

    this.scoreBg = this.add.image(600, 75, "scoreBg").setScale(0.055, 0.045);
    this.scoreBgT = this.add.image(655, 75, "scoreBg").setScale(0.055, 0.045);
    this.timeBg = this.add.image(895, 75, "timeBg").setScale(0.1, 0.045);

    this.puntajeUno = 0;
    this.puntajeDos = 0;

    this.textPlayerOne = this.add.text(490, 75, playerOne, { fontFamily: "Archivo Black", fontSize: "1.8em", fill: "white" }).setOrigin(0.5);
    this.textPlayerTwo = this.add.text(765, 75, playerTwo, { fontFamily: "Archivo Black", fontSize: "1.8em", fill: "white" }).setOrigin(0.5);
    this.scorePlayerOne = this.add.text(600, 79, "0", { fontFamily: "Poppins", fontSize: "4em", fill: "#2357E2" }).setOrigin(0.5);
    this.scorePlayerTwo = this.add.text(655, 79, "0", { fontFamily: "Poppins", fontSize: "4em", fill: "#2357E2" }).setOrigin(0.5);

    tiempoTexto = this.add.text(895, 79, "1:00", { fontFamily: "Poppins", fontSize: "3.5em", fill: "#2357E2" }).setOrigin(0.5);

    const gameOverScreen = this.add.image(0, 0, "gameOverScreen").setOrigin(0).setVisible(false);
    const gameOverText = this.add.image(640, 500, 'gameOverText').setVisible(false);

    this.timerEvent = this.time.addEvent({
      delay: 1000,
      callback: () => {
        tiempoRestante--;
        if (tiempoRestante < 0) {
          tiempoRestante = 0;

          gameOverScreen.setVisible(true);
          gameOverScreen.setAlpha(0);
          gameOverText.setVisible(true);

          this.tweens.add({
            targets: gameOverScreen,
            alpha: 1,
            duration: 1000,
            ease: 'Linear',
          });

          this.tweens.add({
            targets: gameOverText,
            y: 350,
            duration: 1000,
            ease: 'Sine.inOut',
            yoyo: true,
            loop: -1
          });

          this.ball.body.collisionFilter.group = -1;
          this.golPlayerOne.body.collisionFilter.group = -1;
          this.golPlayerTwo.body.collisionFilter.group = -1;
          

          this.time.delayedCall(5000, () => {
            this.scene.start("Winner");
          });
        }
        tiempoTexto.setText(formatoMinutosSegundos(tiempoRestante));
      },
      loop: true,
    });

    // === JUGADOR UNO (FÍSICO) ===
    this.playerOneImage = this.matter.add.image(200, 550, playerOne);
    this.playerOneImage.setScale(0.17);
    this.playerOneImage.setCircle(25);
    this.playerOneImage.setMass(5);
    this.playerOneImage.setFixedRotation();
    this.playerOneImage.setFriction(0.1, 0.03, 0);

    this.matter.world.on("collisionstart", (event) => {
      event.pairs.forEach((pair) => {
        if (
          (pair.bodyA === this.playerOneImage.body && pair.bodyB === this.ball.body) ||
          (pair.bodyA === this.ball.body && pair.bodyB === this.playerOneImage.body)
        ) {
          pair.friction = 0;
          pair.frictionStatic = 0;
        }
      });
    });

    // JUGADOR UNO BOTA
    const bootShapes = this.cache.json.get("playerOneBootShape");

    this.playerOneBoot = this.matter.add.sprite(200, 550, playerOneBoot, null, { shape: bootShapes["playerOneBootShape"] });
    this.playerOneBoot.setFlipX(true);
    this.playerOneBoot.setScale(1.2);
    this.playerOneBoot.setIgnoreGravity(true);
    this.playerOneBoot.setFixedRotation();
    this.playerOneBoot.setAngle(10);
    this.playerOneBoot.setFriction(0, 0, 0);


    // === JUGADOR DOS (FÍSICO) ===
    this.playerTwoImage = this.matter.add.image(1050, 550, playerTwo);
    this.playerTwoImage.setScale(0.17);
    this.playerTwoImage.setCircle(25);
    this.playerTwoImage.setMass(2);
    this.playerTwoImage.setFlipX(true);
    this.playerTwoImage.setFixedRotation();
    this.playerTwoImage.setFriction(0.1, 0.03, 0);

    this.matter.world.on("collisionstart", (event) => {
      event.pairs.forEach((pair) => {
        if (
          (pair.bodyA === this.playerTwoImage.body && pair.bodyB === this.ball.body) ||
          (pair.bodyA === this.ball.body && pair.bodyB === this.playerTwoImage.body)
        ) {
          pair.friction = 0;
          pair.frictionStatic = 0;
        }
      });
    });

    //JUGADOR DOS BOTA
    const bootShapes2 = this.cache.json.get("playerTwoBootShape");

    this.playerTwoBoot = this.matter.add.sprite(200, 550, playerTwoBoot, null, { shape: bootShapes2["playerTwoBootShape"] });
    this.playerTwoBoot.setScale(1.2);
    this.playerTwoBoot.setIgnoreGravity(true);
    this.playerTwoBoot.setFixedRotation();
    this.playerTwoBoot.setAngle(-10);
    this.playerTwoBoot.setFriction(0, 0, 0);

    // === BALÓN (FÍSICO) ===
    this.time.addEvent({
      delay: 0, // cada 2 segundos
      callback: () => {
        let forceX = Phaser.Math.FloatBetween(-0.003, 0.003);
        let forceY = Phaser.Math.FloatBetween(-0.001, -0.005);
        this.ball.applyForce({ x: forceX, y: forceY });
      },
    });

    this.ball = this.matter.add.image(640, 250, "ball");
    this.ball.setScale(0.05);
    this.ball.setCircle(13.5);
    this.ball.setBounce(0.7);
    this.ball.setMass(0.2);
    this.ball.setFriction(0.5, 0.001, 0); // (superficie, aire, que tanto le cuesta moverse)

    // === PORTERÍAS (SOLO VISUALES) ===
    this.add.image(75, 495, "porteriaUno").setScale(1.2, 1.25);
    this.add.image(1205, 495, "porteriaDos").setScale(1.2, 1.25);

    // === INPUT TECLADO ===
    this.cursors = this.input.keyboard.createCursorKeys();
    this.keys = this.input.keyboard.addKeys({
      up: Phaser.Input.Keyboard.KeyCodes.W,
      left: Phaser.Input.Keyboard.KeyCodes.A,
      right: Phaser.Input.Keyboard.KeyCodes.D,
    });

    //PORTERIAS COLISIONES
    this.paredPorteria = this.matter.add.image(60, 443, null, null, { isStatic: true }).setScale(4, 0.06);
    this.paredPorteria.setVisible(false);
    this.paredPorteria.setRotation(Phaser.Math.DegToRad(5));
    this.paredPorteria.setFriction(0, 0, 0);

    this.paredPorteria1 = this.matter.add.image(35, 525, null, null, { isStatic: true }).setScale(5, 0.06);
    this.paredPorteria1.setVisible(false);
    this.paredPorteria1.setRotation(Phaser.Math.DegToRad(-80));

    this.paredPorteria2 = this.matter.add.image(1220, 443, null, null, { isStatic: true }).setScale(4, 0.06);
    this.paredPorteria2.setVisible(false);
    this.paredPorteria2.setRotation(Phaser.Math.DegToRad(-5));
    this.paredPorteria2.setFriction(0, 0, 0);

    this.paredPorteria3 = this.matter.add.image(1245, 525, null, null, { isStatic: true }).setScale(5, 0.06);
    this.paredPorteria3.setVisible(false);
    this.paredPorteria3.setRotation(Phaser.Math.DegToRad(80));

    //PAREDES COLISIONES
    this.paredMarco = this.matter.add.image(20, 400, null, null, { isStatic: true }).setScale(15, 0.06);
    this.paredMarco.setVisible(false);
    this.paredMarco.setRotation(Phaser.Math.DegToRad(90));
    this.paredMarco.setFriction(0, 0, 0);

    this.paredMarco1 = this.matter.add.image(100, 90, null, null, { isStatic: true }).setScale(7, 0.06);
    this.paredMarco1.setVisible(false);
    this.paredMarco1.setRotation(Phaser.Math.DegToRad(-41.5));
    this.paredMarco1.setFriction(0, 0, 0);

    this.paredMarco2 = this.matter.add.image(1175, 90, null, null, { isStatic: true }).setScale(7, 0.06);
    this.paredMarco2.setVisible(false);
    this.paredMarco2.setRotation(Phaser.Math.DegToRad(41.5));
    this.paredMarco2.setFriction(0, 0, 0);

    this.paredMarco3 = this.matter.add.image(640, 11, null, null, { isStatic: true }).setScale(28.5, 0.06);
    this.paredMarco3.setVisible(false);
    this.paredMarco3.setFriction(0, 0, 0);

    this.paredMarco4 = this.matter.add.image(1260, 400, null, null, { isStatic: true }).setScale(15, 0.06);
    this.paredMarco4.setVisible(false);
    this.paredMarco4.setRotation(Phaser.Math.DegToRad(90));
    this.paredMarco4.setFriction(0, 0, 0);

    //COLISIONES GOL
    /* this.golPlayerOne.setSensor(true); */
    this.golPlayerOne = this.matter.add.image(87, 530, null, null, { isStatic: true, isSensor: true, label: "golPlayerOne" }).setScale(4.5, 0.06);
    this.golPlayerOne.setVisible(false);
    this.golPlayerOne.setRotation(Phaser.Math.DegToRad(90));

    this.golPlayerTwo = this.matter.add.image(1193, 530, null, null, { isStatic: true, isSensor: true, label: "golPlayerTwo" }).setScale(4.5, 0.06);
    this.golPlayerTwo.setVisible(false);
    this.golPlayerTwo.setRotation(Phaser.Math.DegToRad(90));

    this.matter.world.on("collisionstart", (event) => {
      event.pairs.forEach((pair) => {
        const bodyA = pair.bodyA;
        const bodyB = pair.bodyB;

        // Revisa si la pelota tocó alguno de los sensores
        if ((bodyA === this.ball.body && bodyB.label === "golPlayerOne") ||
          (bodyB === this.ball.body && bodyA.label === "golPlayerOne")) {
          this.puntajeUno += 1;
          this.scorePlayerTwo.setText(this.puntajeUno);
          this.ball.body.collisionFilter.group = -1;
          this.golPlayerOne.body.collisionFilter.group = -1;



          this.time.addEvent({
            delay: 2000,
            callback: () => {
              this.ball.setPosition(640, 250);
              this.ball.setVelocity(0, 0);
              this.playerOneImage.setPosition(200, 550);
              this.playerTwoImage.setPosition(1050, 550);
              let forceX = Phaser.Math.FloatBetween(-0.003, -0.001);
              let forceY = Phaser.Math.FloatBetween(-0.001, -0.005);
              this.ball.applyForce({ x: forceX, y: forceY });
              this.ball.body.collisionFilter.group = 1;
              this.golPlayerOne.body.collisionFilter.group = 1;
            },
          });
        }

        if ((bodyA === this.ball.body && bodyB.label === "golPlayerTwo") ||
          (bodyB === this.ball.body && bodyA.label === "golPlayerTwo")) {
          this.puntajeDos += 1;
          this.scorePlayerOne.setText(this.puntajeDos);
          this.ball.body.collisionFilter.group = -1;
          this.golPlayerTwo.body.collisionFilter.group = -1;


          this.time.addEvent({
            delay: 2000,
            callback: () => {
              this.ball.setPosition(640, 250);
              this.ball.setVelocity(0, 0);
              this.playerOneImage.setPosition(200, 550);
              this.playerTwoImage.setPosition(1050, 550);
              let forceX = Phaser.Math.FloatBetween(0.003, 0.001);
              let forceY = Phaser.Math.FloatBetween(-0.001, -0.005);
              this.ball.applyForce({ x: forceX, y: forceY });
              this.ball.body.collisionFilter.group = 1;
              this.golPlayerOne.body.collisionFilter.group = 1;
            },
          });
        }
      });
    });

    //COLISIONES ENTIDADES
    this.playerOneImage.body.collisionFilter.group = -1;
    this.playerOneBoot.body.collisionFilter.group = -1;

    this.playerTwoImage.body.collisionFilter.group = -1;
    this.playerTwoBoot.body.collisionFilter.group = -1;


    //BOTA UNO FUNCIONALIDAD
    // Tecla espacio
    this.spaceKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.SPACE);

    // Radio y centro de la rotación (posición relativa del pie al jugador)
    this.bootRadius = 30; // distancia del pie al jugador
    this.bootAngle = Math.PI / 1.7;   // ángulo inicial en radianes
    this.bootBaseAngle = this.bootAngle

    // Actualizar pie en cada frame para que siempre siga al jugador
    this.events.on("update", () => {
      this.bootCenterX = this.playerOneImage.x;
      this.bootCenterY = this.playerOneImage.y;

      // Calcular nueva posición en función del ángulo actual
      this.playerOneBoot.setPosition(
        this.bootCenterX + Math.cos(this.bootAngle) * this.bootRadius,
        this.bootCenterY + Math.sin(this.bootAngle) * this.bootRadius
      );
    });

    // Detectar presionar y soltar espacio
    this.spaceKey.on("down", () => {
      // Animar pie en arco (hacia arriba)
      this.tweens.add({
        targets: this,
        bootAngle: this.bootBaseAngle - Math.PI / 1.8, // rotar 90° hacia arriba
        duration: 200,
        ease: "Sine.easeOut"
      });

      this.tweens.add({
        targets: this.playerOneBoot,
        angle: -90,   // rotar el sprite suavemente
        duration: 150,
        ease: "Sine.easeOut"
      });
    });

    this.spaceKey.on("up", () => {
      // Volver al ángulo original
      this.tweens.add({
        targets: this,
        bootAngle: this.bootBaseAngle, // vuelve a la posición base
        duration: 300,
        ease: "Sine.easeIn"
      });

      this.tweens.add({
        targets: this.playerOneBoot,
        angle: 10,   // rotar el sprite suavemente
        duration: 350,
        ease: "Sine.easeOut"
      });
    });

    //BOTA DOS FUNCIONALIDAD
    this.spaceKeyTwo = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.P);

    // Radio y centro de la rotación (posición relativa del pie al jugador)
    this.bootRadiusTwo = 30; // distancia del pie al jugador 2
    this.bootAngleTwo = Math.PI / 2.5;   // ángulo inicial en radianes
    this.bootBaseAngleTwo = this.bootAngleTwo;

    // Actualizar pie en cada frame para que siempre siga al jugador 2
    this.events.on("update", () => {
      this.bootCenterXTwo = this.playerTwoImage.x;
      this.bootCenterYTwo = this.playerTwoImage.y;

      // Calcular nueva posición en función del ángulo actual
      this.playerTwoBoot.setPosition(
        this.bootCenterXTwo + Math.cos(this.bootAngleTwo) * this.bootRadiusTwo,
        this.bootCenterYTwo + Math.sin(this.bootAngleTwo) * this.bootRadiusTwo
      );
    });

    // Detectar presionar y soltar tecla para Player Two
    this.spaceKeyTwo.on("down", () => {
      // Animar pie en arco (hacia arriba)
      this.tweens.add({
        targets: this,
        bootAngleTwo: this.bootBaseAngleTwo - Math.PI / -1.8,
        duration: 200,
        ease: "Sine.easeOut"
      });

      this.tweens.add({
        targets: this.playerTwoBoot,
        angle: 90,   // rotar sprite suavemente
        duration: 150,
        ease: "Sine.easeOut"
      });
    });

    this.spaceKeyTwo.on("up", () => {
      // Volver al ángulo original
      this.tweens.add({
        targets: this,
        bootAngleTwo: this.bootBaseAngleTwo,
        duration: 300,
        ease: "Sine.easeIn"
      });

      this.tweens.add({
        targets: this.playerTwoBoot,
        angle: -10,   // rotar sprite suavemente
        duration: 350,
        ease: "Sine.easeOut"
      });
    });

    //FIN FUNCIONALIDAD BOTAS

    this.playerOneIsOnGround = false;
    this.playerTwoIsOnGround = false;

    this.matter.world.on('collisionstart', (event) => {
      event.pairs.forEach(pair => {
        const bodies = [pair.bodyA, pair.bodyB];

        // Para jugador uno
        if (bodies.some(b => b.label === 'ground') && bodies.some(b => b === this.playerOneImage.body)) {
          this.playerOneIsOnGround = true;
        }
        // Para jugador dos
        if (bodies.some(b => b.label === 'ground') && bodies.some(b => b === this.playerTwoImage.body)) {
          this.playerTwoIsOnGround = true;
        }
      });
    });

    this.matter.world.on('collisionend', (event) => {
      event.pairs.forEach(pair => {
        const bodies = [pair.bodyA, pair.bodyB];

        // Para jugador uno
        if (bodies.some(b => b.label === 'ground') && bodies.some(b => b === this.playerOneImage.body)) {
          this.playerOneIsOnGround = false;
        }
        // Para jugador dos
        if (bodies.some(b => b.label === 'ground') && bodies.some(b => b === this.playerTwoImage.body)) {
          this.playerTwoIsOnGround = false;
        }
      });
    });

    //PAUSE SCREEN
    let pauseS = this.add.image(0, 0, "pauseScreen").setOrigin(0).setVisible(false);
    pauseS.setDisplaySize(1280, 720);
    pauseS.setAlpha(0.9);

    //PAUSA
    this.isPaused = false;

    this.pause = this.add
      .image(970, 675, "pausa")
      .setInteractive({ useHandCursor: true })
      .on("pointerdown", () => {
        this.isPaused = !this.isPaused;
        if (this.isPaused) {
          // PAUSAR el motor de física y mostrar imagen
          this.matter.world.pause();
          pauseS.setVisible(true);
          this.timerEvent.paused = true;
          this.pause.setTexture('reanudar');
        } else {
          // REANUDAR el motor y ocultar imagen
          this.matter.world.resume();
          pauseS.setVisible(false);
          this.timerEvent.paused = false;
          this.pause.setTexture('pausa');
        }
      })
      .setScale(0.15);

    //BOTONES

    this.music = this.add
      .image(490, 675, "music")
      .setInteractive({ useHandCursor: true })
      .on("pointerdown", () => this.activateMusic(1))
      .setScale(0.17);

    this.sound = this.add
      .image(830, 675, "sound")
      .setInteractive({ useHandCursor: true })
      .on("pointerdown", () => this.activateSound(1))
      .setScale(0.17);

    this.menu = this.add
      .image(1150, 675, "menu")
      .setInteractive({ useHandCursor: true })
      .on("pointerdown", () => this.scene.start("Start"))
      .setScale(0.15);
  }

  activateMusic(direction) {
    this.currentIndexMusic += direction;
    if (this.currentIndexMusic < 0) this.currentIndexMusic = this.musica.length - 1;
    else if (this.currentIndexMusic >= this.musica.length) this.currentIndexMusic = 0;
    this.music.setTexture(this.musica[this.currentIndexMusic]);
  }

  activateSound(direction) {
    this.currentIndexSound += direction;
    if (this.currentIndexSound < 0) this.currentIndexSound = this.sonido.length - 1;
    else if (this.currentIndexSound >= this.sonido.length) this.currentIndexSound = 0;
    this.sound.setTexture(this.sonido[this.currentIndexSound]);
  }

  update(time, delta) {

    // === CONTROLES JUGADOR DOS (CURSORS) === 
    if (this.cursors.right.isDown) { this.playerTwoImage.setVelocityX(4.5); }
    else if (this.cursors.left.isDown) { this.playerTwoImage.setVelocityX(-4.5); }
    if (Phaser.Input.Keyboard.JustDown(this.cursors.up) && this.playerTwoIsOnGround) {
      this.playerTwoImage.setVelocityY(-6); // fuerza de salto 
    }

    // === CONTROLES JUGADOR UNO (WASD) === 
    if (this.keys.right.isDown) { this.playerOneImage.setVelocityX(4.5); }
    else if (this.keys.left.isDown) { this.playerOneImage.setVelocityX(-4.5); }
    if (Phaser.Input.Keyboard.JustDown(this.keys.up) && this.playerOneIsOnGround) {
      this.playerOneImage.setVelocityY(-6); // fuerza de salto 
    }
  }
  /* update(time, delta) { // === CONTROLES JUGADOR DOS (CURSORS) === 
    if (this.cursors.right.isDown) { this.playerTwoImage.setVelocityX(5); }
    else if (this.cursors.left.isDown) { this.playerTwoImage.setVelocityX(-5); }
    if (Phaser.Input.Keyboard.JustDown(this.cursors.up) && this.playerTwoImage.body.velocity.y === 0) {
      this.playerTwoImage.setVelocityY(-5); // fuerza de salto 
    }

    // === CONTROLES JUGADOR UNO (WASD) === 
    if (this.keys.right.isDown) { this.playerOneImage.setVelocityX(5); }
    else if (this.keys.left.isDown) { this.playerOneImage.setVelocityX(-5); }
    if (Phaser.Input.Keyboard.JustDown(this.keys.up) && this.playerOneImage.body.velocity.y === 0) {
      this.playerOneImage.setVelocityY(-5); // fuerza de salto 
    }
  } */
}

