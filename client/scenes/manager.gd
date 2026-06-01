extends Node

signal todo_list_received(payload: Dictionary)

const HTTP_BASE_URL = "http://127.0.0.1:8000/v1"
const WS_BASE_URL = "ws://127.0.0.1:8000/v1/ws"

var today = 1

func advance_day() -> void:
    today += 1

func notify_todo_list_received(payload: Dictionary) -> void:
    todo_list_received.emit(payload)

func get_today() -> int:
    return today