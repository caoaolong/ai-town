extends Area2D

signal _debug_walk(world_pos: Vector2)


func _input(event: InputEvent) -> void:
    if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
        var world_pos := get_global_mouse_position()
        var space := get_world_2d().direct_space_state
        var q := PhysicsPointQueryParameters2D.new()
        q.position = world_pos
        q.collision_mask = 0xFFFFFFFF
        q.collide_with_areas = true
        for hit in space.intersect_point(q):
            if hit.collider == self:
                print("Debug walk to: ", world_pos)
                _debug_walk.emit(world_pos)
                return
