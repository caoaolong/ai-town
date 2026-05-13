extends ProgressBar

class_name TimeBar

@export var running: bool = false

func start() -> void:
    running = true

func stop() -> void:
    running = false

func _on_timer_timeout() -> void:
    if running and value < max_value:
        value += step
