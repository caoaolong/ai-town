extends MarginContainer

var player: AgentPlayer = null


func _on_send_state_pressed() -> void:
    if player == null:
        return
    player.create_todolist()

func _on_update_camera_target(new_target: AgentPlayer) -> void:
    player = new_target

func _on_test_move_pressed() -> void:
    pass


func _on_debug_walk(world_pos: Vector2) -> void:
    if player == null:
        return
    player.move_to(world_pos)
