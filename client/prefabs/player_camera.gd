extends Camera2D

class_name PlayerCamera

## 要跟随的目标节点
@export var target: AgentPlayer

## 跟随的缓动速度（越小越慢，越大越快）
@export var follow_speed: float = 5.0

func update_follow_target(new_target: AgentPlayer) -> void:
    target.hide_arrow()
    target = new_target
    target.show_arrow()


func _process(delta: float) -> void:
    if target == null:
        return
    
    # 使用 lerp 实现缓动跟随
    var target_position = target.global_position
    global_position = global_position.lerp(target_position, follow_speed * delta)
