export class PlayerOne extends Phaser.Physics.Arcade.Sprite
{
    constructor(scene, x, y, type){
        super(scene, x, y, type);
        scene.add.existing(this);
        scene.physics.add.existing(this);
    }
}