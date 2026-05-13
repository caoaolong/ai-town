extends MarginContainer

var player: AgentPlayer = null


func _on_send_state_pressed() -> void:
    if player != null:
        var state = player.create_state()
        player.send_state(Config.EV_CONTEXT, state)

func _on_update_camera_target(new_target: AgentPlayer) -> void:
    player = new_target

func _on_test_move_pressed() -> void:
    if player == null:
        return
    var context = Schema.Context.new()
    context.direction = Config.DIRECTIONS.pick_random()
    player.goto_target(context)
