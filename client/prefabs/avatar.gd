extends TextureButton

class_name Avatar

signal focus_player(player: AgentPlayer)

var player: AgentPlayer = null

func set_avatar(new_player: AgentPlayer, _button_group: ButtonGroup, _pressed: bool = false) -> void:
    player = new_player
    self.button_group = _button_group
    self.toggle_mode = true
    self.button_pressed = _pressed
    var value = get_node("Value") as TextureRect
    value.texture = new_player.avatar


func _on_toggled(toggled_on: bool) -> void:
    if toggled_on:
        focus_player.emit(player)
