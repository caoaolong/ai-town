extends Camera2D

class_name PlayerCamera

## 要跟随的目标节点
@export var target: AgentPlayer

## 跟随的缓动速度（越小越慢，越大越快）
@export var follow_speed: float = 5.0

## 缩放速度
@export var zoom_speed: float = 0.1

## 最小缩放值
@export var min_zoom: float = 0.5

## 最大缩放值
@export var max_zoom: float = 1.5

func update_follow_target(new_target: AgentPlayer) -> void:
    target.hide_arrow()
    target = new_target
    target.show_arrow()


func _unhandled_input(event: InputEvent) -> void:
    if event is InputEventMouseButton and event.pressed:
        if event.button_index == MOUSE_BUTTON_WHEEL_UP:
            var new_zoom = zoom.x + zoom_speed
            new_zoom = clampf(new_zoom, min_zoom, max_zoom)
            zoom = Vector2(new_zoom, new_zoom)
        elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
            var new_zoom = zoom.x - zoom_speed
            new_zoom = clampf(new_zoom, min_zoom, max_zoom)
            zoom = Vector2(new_zoom, new_zoom)

func _process(delta: float) -> void:
    if target == null:
        return
    
    # 使用 lerp 实现缓动跟随
    var target_position = target.global_position
    global_position = global_position.lerp(target_position, follow_speed * delta)
