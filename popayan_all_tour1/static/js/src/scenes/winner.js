export class Winner extends Phaser.Scene {
  constructor() {
    super("Winner");
  }

  preload() {
    //jugadores
    this.load.image("Diablito", "/static/assets/diablito.png");
    this.load.image("Sahumadora", "/static/assets/sahumadora.png");
    this.load.image("Parroco", "/static/assets/parroco.png");
    this.load.image("Sabio Caldas", "/static/assets/sabiocaldas.png");
    this.load.image("Carguero", "/static/assets/carguero.png");
    this.load.image("Chirimia", "/static/assets/chirimia.png");
    //botas jugadores
    this.load.image("BotaDiablito", "/static/assets/bota_diablito.png");
    this.load.image("BotaSahumadora", "/static/assets/bota_sahumadora.png");
    this.load.image("BotaParroco", "/static/assets/bota_parroco.png");
    this.load.image("BotaCaldas", "/static/assets/bota_caldas.png");
    this.load.image("BotaCarguero", "/static/assets/bota_carguero.png");
    this.load.image("BotaChirimia", "/static/assets/bota_chirimia.png");
    //estadios
    this.load.image("estadioDia", "/static/assets/stadiumDay.png");
    this.load.image("estadioTarde", "/static/assets/stadiumEvenning.png");
    this.load.image("estadioNoche", "/static/assets/stadiumNigth.png");
    //premiacion
    this.load.image("trophy", "/static/assets/trofeo.png");
    this.load.image("premiacion", "/static/assets/premiacion.png");
    this.load.image("confettiF", "/static/assets/confetti_falling.png");
    this.load.image("confettiG", "/static/assets/confetti_ground.png");
    this.load.image("title", "/static/assets/title_premiacion.png");
    this.load.image("menuButton", "/static/assets/menu_premiacion.png");
  }

  create() {
    const clima = this.game.registry.get("climaSelected");
    this.stadiums = ["estadioDia", "estadioTarde", "estadioNoche"];
    const playerOne = this.game.registry.get("playerOneSelected");
    const playerTwo = this.game.registry.get("playerTwoSelected");
    const playerOneBoot = this.game.registry.get("playerOneBootS");
    const playerTwoBoot = this.game.registry.get("playerTwoBootS");

    let background = this.add.image(0, 0, clima).setOrigin(0);
    background.setDisplaySize(1280, 720);

    const conffetiG = this.add.image(640, 650, "confettiG")
    conffetiG.setDisplaySize(900, 100);
    conffetiG.setAlpha(0);

    this.tweens.add({
      targets: conffetiG,
      alpha: 1,
      duration: 10000,
      ease: 'Linear',
    });

    let premiacion = this.add.image(240, 350, "premiacion").setOrigin(0);
    premiacion.setScale(1);

    this.playerOneImage = this.add.image(470, 550, "Diablito");
    this.playerOneImage.setScale(0.20);
    this.playerOneImage.setFlipX(true);

    this.playerOneBoot = this.add.image(485, 580, "BotaDiablito", null);
    this.playerOneBoot.setScale(1.2);
    this.playerOneBoot.setAngle(-20);

    const trophy = this.add.image(430, 530, "trophy");
    trophy.setScale(0.17);
    trophy.setAngle(10);

    this.tweens.add({
      targets: trophy,
      y: 500,
      duration: 1500,
      ease: 'Sine.inOut',
      yoyo: true,
      loop: -1
    });

    this.playerTwoImage = this.add.image(800, 580, "Sahumadora");
    this.playerTwoImage.setScale(0.20);
    this.playerTwoImage.setFlipX(true);

    this.playerTwoBoot = this.add.image(815, 615, "BotaSahumadora", null);
    this.playerTwoBoot.setScale(1.2);
    this.playerTwoBoot.setAngle(-20);

    const conffetiF = this.add.image(0, -100, "confettiF").setOrigin(0);
    conffetiF.setDisplaySize(1280, 1000);

    this.tweens.add({
      targets: conffetiF,
      y: 0,
      duration: 2000,
      ease: 'Sine.inOut',
      yoyo: true,
    });

    this.tweens.add({
      targets: conffetiF,
      alpha: 0,
      duration: 2000,
      ease: 'Linear',
    });

    const title = this.add.image(640, 200, "title");
    title.setScale(0.4);
    this.tweens.add({
      targets: title,
      y: 120,
      duration: 1000,
      ease: 'Sine.inOut',
    });

    const menu = this.add.image(640, 250, "menuButton").setInteractive({ useHandCursor: true });
    menu.setScale(0.2);
    menu.on('pointerdown', () => {
            this.scene.start('Start');
        });
  }

  update() {

  }
}