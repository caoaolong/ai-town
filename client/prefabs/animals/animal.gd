extends Node2D

@onready var animated_sprited_2d: AnimatedSprite2D = $AnimatedSprite2D

func _ready() -> void:
    animated_sprited_2d.flip_h = randf() < 0.5