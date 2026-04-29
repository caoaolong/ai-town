extends Node2D

signal update_players(players: Array[AgentPlayer])

@onready var player_group: Node2D = $Players
@onready var player_camera: PlayerCamera = $PlayerCamera

@export var chat_scene: ChatControl

func _ready() -> void:
    chat_scene.update_camera_target.connect(_on_update_camera_target)

    await get_tree().process_frame
    emit_signal("update_players", player_group.get_children())


func _on_update_camera_target(new_target: AgentPlayer) -> void:
    player_camera.update_follow_target(new_target)
