extends Control

class_name ChatControl

signal update_camera_target(new_target: AgentPlayer)

@onready var avatar_container: HBoxContainer = $VBoxContainer/AvatarContainer
@onready var debug_container: MarginContainer = $VBoxContainer/DebugContainer

@export var game_scene: Node2D
@export var player_avatar: PackedScene

const AVATAR_SCENE := preload("res://prefabs/avatar.tscn")

var avatar_button_group: ButtonGroup

func _ready():
    avatar_button_group = ButtonGroup.new()
    avatar_button_group.pressed.connect(_on_avatar_button_pressed)
    # 连接信号
    game_scene.update_players.connect(_on_update_players)
    # 连接调试界面信号
    update_camera_target.connect(debug_container._on_update_camera_target)

func _on_update_players(_players):
    for i in range(_players.size()):
        var player = _players[i]
        var avatar = AVATAR_SCENE.instantiate()
        avatar.set_avatar(player, avatar_button_group, i == 0)
        if i == 0:
            emit_signal("update_camera_target", player)
        avatar_container.add_child(avatar)


func _on_avatar_button_pressed(button: BaseButton):
    var avatar = button as Avatar
    if avatar and avatar.player != null:
        emit_signal("update_camera_target", avatar.player)
