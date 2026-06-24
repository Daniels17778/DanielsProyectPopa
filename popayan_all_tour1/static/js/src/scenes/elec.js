export class Elec extends Phaser.Scene {

    constructor() {
        super('Elec');
    }

    preload() {
        //fondo
        this.load.image('backgroundElec', '/static/assets/elec.jpg');
        //personajes
        this.load.image('Diablito', '/static/assets/diablito.png');
        this.load.image('Sahumadora', '/static/assets/sahumadora.png');
        this.load.image('Parroco', '/static/assets/parroco.png');
        this.load.image('Sabio Caldas', '/static/assets/sabiocaldas.png');
        this.load.image('Carguero', '/static/assets/carguero.png');
        this.load.image('Chirimia', '/static/assets/chirimia.png');
        // personajes botas
        this.load.image("BotaDiablito", "/static/assets/bota_diablito.png");
        this.load.image("BotaSahumadora", "/static/assets/bota_sahumadora.png");
        this.load.image("BotaParroco", "/static/assets/bota_parroco.png");
        this.load.image("BotaCaldas", "/static/assets/bota_caldas.png");
        this.load.image("BotaCarguero", "/static/assets/bota_carguero.png");
        this.load.image("BotaChirimia", "/static/assets/bota_chirimia.png");
        //flechas
        this.load.image('derecha', '/static/assets/derecha.png');
        this.load.image('izquierda', '/static/assets/izquierda.png');
        //personajesIconos
        this.load.image('logoDiablito', '/static/assets/diablito_logo.png');
        this.load.image('logoSahumadora', '/static/assets/sahumadora_logo.png');
        this.load.image('logoParroco', '/static/assets/parroco_icono.png');
        this.load.image('logoSabioCaldas', '/static/assets/sabiocaldas - logo.png');
        this.load.image('logoCarguero', '/static/assets/carguero_logo.png');
        this.load.image('logoChirimia', '/static/assets/chirimia_logo.png');
        //fondo estadios
        this.load.image('DiaBg', '/static/assets/DiaBg.png');
        this.load.image('TardeBg', '/static/assets/TardeBg.png');
        this.load.image('NocheBg', '/static/assets/NocheBg.png');
        //climas/static/
        this.load.image('Dia', '/static/assets/Dia.png');
        this.load.image('Tarde', '/static/assets/Tarde.png');
        this.load.image('Noche', '/static/assets/Noche.png');
        //estadios
        this.load.image('estadioDia', '/static/assets/stadiumDay.png');
        this.load.image('estadioTarde', '/static/assets/stadiumEvenning.png');
        this.load.image('estadioNoche', '/static/assets/stadiumNigth.png');

    }

    create() {
        let background = this.add.image(0, 0, 'backgroundElec').setOrigin(0);
        background.setDisplaySize(1280, 720);

        //personajes
        this.characters = ['Diablito', 'Sahumadora', 'Parroco', 'Sabio Caldas', 'Carguero', 'Chirimia'];
        this.boots = ['BotaDiablito', 'BotaSahumadora', 'BotaParroco', 'BotaCaldas', 'BotaCarguero', 'BotaChirimia'];
        this.colors = [0xB8001C, 0x890015, 0x23B14C, 0x211422, 0x4B659E, 0x454545];
        this.charactersImageBg = ['logoDiablito', 'logoSahumadora', 'logoParroco', 'logoSabioCaldas', 'logoCarguero', 'logoChirimia'];
        this.stadiumsBg = ['DiaBg', 'TardeBg', 'NocheBg'];
        this.stadiums = ['Dia', 'Tarde', 'Noche'];
        this.canchas = ['estadioDia', 'estadioTarde', 'estadioNoche']
        this.currentStadium = Phaser.Math.Between(0, this.stadiums.length - 1);
        this.currentIndex = Phaser.Math.Between(0, this.characters.length - 1);
        this.currentIndexR = Phaser.Math.Between(0, this.characters.length - 1);
        this.game.registry.set('playerOneSelected', this.characters[this.currentIndex]);
        this.game.registry.set('playerTwoSelected', this.characters[this.currentIndexR]);
        this.game.registry.set('playerOneBootS', this.boots[this.currentIndex]);
        this.game.registry.set('playerTwoBootS', this.boots[this.currentIndexR]);
        this.game.registry.set('climaSelected', this.canchas[this.currentStadium]);

        //fondo blue
        const blueBg = this.add.graphics();
        blueBg.fillStyle(0x2357E2, 1);
        blueBg.fillRoundedRect(255, 170, 770, 350, {
            tl: 10,   // top-left
            tr: 10,    // top-right
            bl: 10,    // bottom-left
            br: 10    // bottom-right
        });


        //Fondo jugar
        const playBg = this.add.graphics();
        playBg.fillStyle(0xffffff, 1);
        playBg.fillRoundedRect(340, 170, 685, 300, {
            tl: 0,   // top-left
            tr: 10,    // top-right
            bl: 0,    // bottom-left
            br: 0    // bottom-right
        });

        //Fondo menu
        const menuBg = this.add.graphics();
        menuBg.fillStyle(0x2357E2, 1);
        menuBg.fillRoundedRect(255, 170, 85, 70, {
            tl: 10,   // top-left
            tr: 0,    // top-right
            bl: 0,    // bottom-left
            br: 0    // bottom-right
        });

        //boton menu
        this.leftArrowL = this.add.image(295, 205, 'izquierda').setInteractive({ useHandCursor: true }).on('pointerdown', () => this.scene.start('Start'));
        this.leftArrowL.setScale(0.03);

        //Título
        const elecText = this.add.text(645, 205, 'ELECCIÓN DE PERSONAJE', {
            fontFamily: 'Archivo Black',
            fontSize: '3em',
            fill: '#2357E2'
        }).setOrigin(0.5);

        //fondo personaje L
        this.playerOneBg = this.add.graphics();
        this.playerOneBg.fillStyle(this.colors[this.currentIndex]);
        this.playerOneBg.fillRoundedRect(255, 240, 240, 270, {
            tl: 0,   // top-left
            tr: 0,    // top-right
            bl: 0,    // bottom-left
            br: 0    // bottom-right
        });

        //nombre del personaje L
        this.textPlayerOne = this.add.text(375, 460, this.characters[this.currentIndex], { fontFamily: 'Archivo Black', fontSize: '2.7em', fill: 'white' }).setOrigin(0.5);
        this.playerOneName = this.add.text(375, 290, 'Jugador 1', { fontFamily: 'Archivo Black', fontSize: '2.7em', fill: 'white' }).setOrigin(0.5);

        //imagen de fondo personaje L
        this.characterImageBgL = this.add.image(375, 390, this.charactersImageBg[this.currentIndex]).setOrigin(0.5);
        this.characterImageBgL.setScale(0.3);
        this.characterImageBgL.setAlpha(0.15);

        //imagen del personaje L
        this.characterImageL = this.add.image(375, 380, this.characters[this.currentIndex]);
        this.characterImageL.setScale(0.3);
        this.tweens.add({
            targets: this.characterImageL,
            y: 370,
            duration: 1500,
            ease: 'Sine.inOut',
            yoyo: true,
            loop: -1
        });

        // flechas personaje L
        this.leftArrowL = this.add.image(290, 380, 'izquierda').setInteractive({ useHandCursor: true }).on('pointerdown', () => this.changeCharacterL(-1));
        this.leftArrowL.setScale(0.03);
        this.rightArrowL = this.add.image(460, 380, 'derecha').setInteractive({ useHandCursor: true }).on('pointerdown', () => this.changeCharacterL(1));
        this.rightArrowL.setScale(0.03);

        //fondo personaje R
        this.playerTwoBg = this.add.graphics();
        this.playerTwoBg.fillStyle(this.colors[this.currentIndexR]);
        this.playerTwoBg.fillRoundedRect(785, 240, 240, 270, {
            tl: 0,   // top-left
            tr: 0,    // top-right
            bl: 0,    // bottom-left
            br: 0    // bottom-right
        });

        //nombre del personaje R
        this.playerTwoName = this.add.text(900, 290, 'Jugador 2', { fontFamily: 'Archivo Black', fontSize: '2.7em', fill: 'white' }).setOrigin(0.5);
        this.textPlayerTwo = this.add.text(900, 460, this.characters[this.currentIndexR], { fontFamily: 'Archivo Black', fontSize: '2.7em', fill: 'white' }).setOrigin(0.5);

        //imagen de fondo del personaje R
        this.characterImageBgR = this.add.image(900, 390, this.charactersImageBg[this.currentIndexR]).setOrigin(0.5);
        this.characterImageBgR.setScale(0.3);
        this.characterImageBgR.setAlpha(0.15);

        //imagen del personaje R
        this.characterImageR = this.add.image(900, 380, this.characters[this.currentIndexR]);
        this.characterImageR.setScale(0.3);
        this.characterImageR.setFlipX(true);
        this.tweens.add({
            targets: this.characterImageR,
            y: 370,
            duration: 1500,
            ease: 'Sine.inOut',
            yoyo: true,
            loop: -1
        });

        // Flechas personaje R
        this.leftArrowR = this.add.image(820, 380, 'izquierda').setInteractive({ useHandCursor: true }).on('pointerdown', () => this.changeCharacterR(-1));
        this.leftArrowR.setScale(0.03);
        this.rightArrowR = this.add.image(980, 380, 'derecha').setInteractive({ useHandCursor: true }).on('pointerdown', () => this.changeCharacterR(1));
        this.rightArrowR.setScale(0.03);

        //fondo estadio
        this.stadiumBg = this.add.image(640, 375, this.stadiumsBg[this.currentStadium]);
        this.stadiumBg.setScale(0.8, 0.76);

        //Imagen estadio
        this.stadium = this.add.image(640, 380, this.stadiums[this.currentStadium]);
        this.stadium.setScale(0.4);

        //Nombre estadio
        this.textStadium = this.add.text(640, 460, this.stadiums[this.currentStadium], { fontFamily: 'Archivo Black', fontSize: '2.5em', fill: 'white' }).setOrigin(0.5);
        this.nameStadium = this.add.text(640, 290, 'Hora', { fontFamily: 'Archivo Black', fontSize: '2.5em', fill: 'white' }).setOrigin(0.5);

        //Flechas estadio
        this.leftArrowS = this.add.image(550, 380, 'izquierda').setInteractive({ useHandCursor: true }).on('pointerdown', () => this.changeStadiums(-1));
        this.leftArrowS.setScale(0.03);
        this.rightArrowS = this.add.image(725, 380, 'derecha').setInteractive({ useHandCursor: true }).on('pointerdown', () => this.changeStadiums(1));
        this.rightArrowS.setScale(0.03);

        //play fondo
        const play = this.add.graphics();
        play.fillStyle(0x2357E2, 1);
        play.fillRoundedRect(492, 510, 296, 70, {
            tl: 0,   // top-left
            tr: 0,    // top-right
            bl: 10,    // bottom-left
            br: 10    // bottom-right
        });

        //play texto
        const playText = this.add.text(640, 545, 'JUGAR', { fontFamily: 'Archivo Black', fontSize: '3em', fill: 'white' }).setOrigin(0.5).setInteractive({ useHandCursor: true }).on('pointerdown', () => this.scene.start('Juego'));
    }

    changeCharacterL(direction) {
        this.currentIndex += direction;

        if (this.currentIndex < 0) {
            this.currentIndex = this.characters.length - 1;
        } else if (this.currentIndex >= this.characters.length) {
            this.currentIndex = 0;
        }

        this.characterImageBgL.setTexture(this.charactersImageBg[this.currentIndex]);
        this.characterImageL.setTexture(this.characters[this.currentIndex]);
        this.textPlayerOne.setText(this.characters[this.currentIndex]);
        this.playerOneBg.clear();
        this.playerOneBg.fillStyle(this.colors[this.currentIndex]);
        this.playerOneBg.fillRoundedRect(255, 240, 240, 270, {
            tl: 0,   // top-left
            tr: 0,    // top-right
            bl: 0,    // bottom-left
            br: 0    // bottom-right
        });

        if (this.currentIndex == 0) {
            this.game.registry.set('playerOneSelected', 'Diablito');
            this.game.registry.set('playerOneBootS', 'BotaDiablito');
        } else if (this.currentIndex == 1) {
            this.game.registry.set('playerOneSelected', 'Sahumadora');
            this.game.registry.set('playerOneBootS', 'BotaSahumadora');
        } else if (this.currentIndex == 2) {
            this.game.registry.set('playerOneSelected', 'Parroco');
            this.game.registry.set('playerOneBootS', 'BotaParroco');
        } else if (this.currentIndex == 3) {
            this.game.registry.set('playerOneSelected', 'Sabio Caldas');
            this.game.registry.set('playerOneBootS', 'BotaCaldas');
        } else if (this.currentIndex == 4) {
            this.game.registry.set('playerOneSelected', 'Carguero');
            this.game.registry.set('playerOneBootS', 'BotaCarguero');
        } else {
            this.game.registry.set('playerOneSelected', 'Chirimia');
            this.game.registry.set('playerOneBootS', 'BotaChirimia');
        }
    }

    changeCharacterR(direction) {
        this.currentIndexR += direction;

        if (this.currentIndexR < 0) {
            this.currentIndexR = this.characters.length - 1;
        } else if (this.currentIndexR >= this.characters.length) {
            this.currentIndexR = 0;
        }

        this.characterImageBgR.setTexture(this.charactersImageBg[this.currentIndexR]);
        this.characterImageR.setTexture(this.characters[this.currentIndexR]);
        this.textPlayerTwo.setText(this.characters[this.currentIndexR]);
        this.playerTwoBg.clear();
        this.playerTwoBg.fillStyle(this.colors[this.currentIndexR]);
        this.playerTwoBg.fillRoundedRect(785, 240, 240, 270, {
            tl: 0,   // top-left
            tr: 0,    // top-right
            bl: 0,    // bottom-left
            br: 0    // bottom-right
        });

        if (this.currentIndexR == 0) {
            this.game.registry.set('playerTwoSelected', 'Diablito');
            this.game.registry.set('playerTwoBootS', 'BotaDiablito');
        } else if (this.currentIndexR == 1) {
            this.game.registry.set('playerTwoSelected', 'Sahumadora');
            this.game.registry.set('playerTwoBootS', 'BotaSahumadora');
        } else if (this.currentIndexR == 2) {
            this.game.registry.set('playerTwoSelected', 'Parroco');
            this.game.registry.set('playerTwoBootS', 'BotaParroco');
        } else if (this.currentIndexR == 3) {
            this.game.registry.set('playerTwoSelected', 'Sabio Caldas');
            this.game.registry.set('playerTwoBootS', 'BotaCaldas');
        } else if (this.currentIndexR == 4) {
            this.game.registry.set('playerTwoSelected', 'Carguero');
            this.game.registry.set('playerTwoBootS', 'BotaCarguero');
        } else {
            this.game.registry.set('playerTwoSelected', 'Chirimia');
            this.game.registry.set('playerTwoBootS', 'BotaChirimia');
        }
    }

    changeStadiums(direction) {
        this.currentStadium += direction;

        if (this.currentStadium < 0) {
            this.currentStadium = this.stadiums.length - 1;
        } else if (this.currentStadium >= this.stadiums.length) {
            this.currentStadium = 0;
        }

        this.stadium.setTexture(this.stadiums[this.currentStadium]);
        this.textStadium.setText(this.stadiums[this.currentStadium]);
        this.stadiumBg.setTexture(this.stadiumsBg[this.currentStadium]);

        if (this.currentStadium == 0) {
            this.game.registry.set('climaSelected', 'estadioDia');
        } else if (this.currentStadium == 1) {
            this.game.registry.set('climaSelected', 'estadioTarde');
        } else {
            this.game.registry.set('climaSelected', 'estadioNoche');
        }
    }

    update() {

    }

}
