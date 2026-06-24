export class Start extends Phaser.Scene {
  constructor() {
    super("Start");
  }

  preload() {
    this.load.image("backgroundD", "/static/assets/menuDay.png");
    this.load.image("backgroundE", "/static/assets/menuEvenning.png");
    this.load.image("backgroundN", "/static/assets/menuNigth.png");
    this.load.image("logo", "/static/assets/title.png");
    this.load.image("playButton", "/static/assets/playButton.png");
    this.load.image("creditButton", "/static/assets/creditButton.png");
    this.load.image("back", "/static/assets/Back.png");
  }

  create() {
    //fondos
    this.fondosKeys = ["backgroundD", "backgroundE", "backgroundN"];
    this.fondos = [];
    this.fondoIndex = 0;

    for (let i = 0; i < this.fondosKeys.length; i++) {
      let fondo = this.add
        .image(0, 0, this.fondosKeys[i])
        .setOrigin(0)
        .setDisplaySize(1280, 720);
      fondo.setAlpha(i === 0 ? 1 : 0);
      this.fondos.push(fondo);
    }

    this.transicionarFondo();

    //Logo
    const logo = this.add.image(640, 240, "logo");
    logo.setScale(0.15);
    this.tweens.add({
      targets: logo,
      y: 220,
      duration: 1500,
      ease: "Sine.inOut",
      yoyo: true,
      loop: -1,
    });

this.leftArrowL = this.add
  .image(135, 105, "back")
  .setScale(0.15)
  .setInteractive({ useHandCursor: true })
  .on("pointerdown", () => {
    window.location.href = window.urlEntretenimiento;
  });


    //Funcionamiento botón jugar
    const playButton = this.add
      .image(640, 450, 250, 60)
      .setInteractive({ useHandCursor: true });
    playButton.setScale(8, 2);
    //Fondo botón jugar
    const playBg = this.add.image(640, 450, "playButton");
    playBg.setScale(0.15);
    //Redirección a elección de personaje
    playButton.on("pointerdown", () => {
      this.scene.start("Elec");
    });

    /* //Funcionamiento botón créditos
        const creditButton = this.add.image(640, 550, 250, 60).setInteractive({ useHandCursor: true });
        creditButton.setScale(8, 2);
        //Fondo botón créditos
        const creditBg = this.add.image(640, 550, 'creditButton');
        creditBg.setScale(0.15);
        //Redirección a créditos
        creditButton.on('pointerdown', () => {
            this.scene.start('Credit');
        }); */
  }

  transicionarFondo() {
    let fondoActual = this.fondos[this.fondoIndex];
    let siguienteIndex = (this.fondoIndex + 1) % this.fondos.length;
    let fondoSiguiente = this.fondos[siguienteIndex];

    // Hacer fade in al siguiente fondo
    this.tweens.add({
      targets: fondoSiguiente,
      alpha: 1,
      duration: 5000,
      ease: "Linear",
      onComplete: () => {
        this.tweens.add({
          targets: fondoActual,
          alpha: 0,
          duration: 5000,
          ease: "Linear",
          onComplete: () => {
            this.fondoIndex = siguienteIndex;

            this.time.delayedCall(1, () => {
              this.transicionarFondo();
            });
          },
        });
      },
    });
  }

  update() {}
}
