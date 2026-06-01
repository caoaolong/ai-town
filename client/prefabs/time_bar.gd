extends ProgressBar

class_name TimeBar

signal completed

@export var running: bool = false

func start() -> void:
    running = true

func stop() -> void:
    running = false

func _on_timer_timeout() -> void:
    if running and value < max_value:
        value += step
        if value >= max_value:
            completed.emit()
            GM.advance_day()
            value = 0
