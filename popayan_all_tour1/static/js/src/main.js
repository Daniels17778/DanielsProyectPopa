import { Start } from "./scenes/Start.js";
import { Elec } from "./scenes/elec.js";
import { Juego } from "./scenes/juego.js";
import { Winner } from "./scenes/winner.js";

const config = {
  type: Phaser.AUTO,
  title: "CiroGoal",
  description: "",
  parent: "game-container",
  width: 1280,
  height: 720,
  backgroundColor: "#000000",
  pixelArt: false,
  scene: [
    Start,
    Elec, 
    Juego,
    Winner
  ],
  scale: {
    mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_BOTH,
  },
  physics: {
    default: "matter",
    matter: {
      debug: false,
      gravity: { y: 0.5 },
      fps: 60,
      iterations: {
        position: 4, // por defecto 6
        velocity: 2, // por defecto 4
      },
    },
  },
};

new Phaser.Game(config);
