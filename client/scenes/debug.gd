extends MarginContainer

var player: AgentPlayer = null


func _on_send_state_pressed() -> void:
    if player != null:
        var state = player.create_state()
        player.send_state("context", state)

func _on_update_camera_target(new_target: AgentPlayer) -> void:
    player = new_target