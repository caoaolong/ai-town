extends CharacterBody2D

class_name AgentPlayer

## 头像
@export var avatar: AtlasTexture
@export var speed: float = 40.0
@onready var road: TileMapLayer = $"../../Road"

@onready var animated_sprite: AnimatedSprite2D = $AnimatedSprite2D
@onready var arrow: Sprite2D = $Arrow

var astar: AStarGrid2D = AStarGrid2D.new()
# 添加 HTTPRequest 节点引用
var http_request: HTTPRequest = HTTPRequest.new()
var current_state: Dictionary = {}

var current_path = []
var path_index = 0
var facing: String = "forward"

func _ready() -> void:
    _build_astar()
    _init_http_request()

func _process(_delta: float) -> void:
    if path_index >= current_path.size():
        velocity = Vector2.ZERO
        _play_animation("idle")
        move_and_slide()
        return
    var target_cell = current_path[path_index]
    var target_world = road.to_global(road.map_to_local(target_cell))
    var dir = target_world - global_position
    if dir.length() < 2:
        path_index += 1
    else:
        velocity = dir.normalized() * speed
        _update_facing(dir)
        _play_animation("run")
    move_and_slide()


func _update_facing(dir: Vector2) -> void:
    if abs(dir.x) > abs(dir.y):
        facing = "right" if dir.x > 0 else "left"
    else:
        facing = "forward" if dir.y > 0 else "backward"

func _play_animation(type: String) -> void:
    var anim_name = type + "_" + facing
    if animated_sprite.sprite_frames.has_animation(anim_name):
        animated_sprite.play(anim_name)

func _build_astar():
    var rect = road.get_used_rect()
    astar.region = rect
    astar.cell_size = Vector2(road.tile_set.tile_size)
    astar.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_NEVER
    astar.update()
    for x in range(rect.position.x, rect.end.x):
        for y in range(rect.position.y, rect.end.y):
            astar.set_point_solid(Vector2i(x, y), true)
    for cell in road.get_used_cells():
        astar.set_point_solid(cell, false)


func move_to(target_world_pos: Vector2):
    var start_cell = road.local_to_map(road.to_local(global_position))

    var end_cell = road.local_to_map(road.to_local(target_world_pos))

    current_path = astar.get_id_path(start_cell, end_cell)

    path_index = 0


func create_todolist():
    _send_http_request("/player/todo_list", HTTPClient.METHOD_POST, {
        "player_id": name,
        "day": GM.get_today()
    })


func show_arrow() -> void:
    arrow.visible = true

func hide_arrow() -> void:
    arrow.visible = false


## 初始化 HTTP 请求节点
func _init_http_request() -> void:
    add_child(http_request)
    http_request.request_completed.connect(_on_http_request_completed)


## 处理 HTTP 请求完成
func _on_http_request_completed(_result: int, _response_code: int, _headers: PackedStringArray, _body: PackedByteArray) -> void:
    if _response_code == 200 and _result == 0:
        var data = JSON.parse_string(_body.get_string_from_utf8())
        if data == null or not (data is Dictionary):
            return
        match data.get("type"):
            "todolist":
                print("create todolist!")
                GM.notify_todo_list_received(data as Dictionary)


## 发送 HTTP 请求
func _send_http_request(endpoint: String, method: HTTPClient.Method=HTTPClient.METHOD_GET, data: Dictionary = {}) -> void:
    var url = GM.HTTP_BASE_URL + endpoint
    var headers = ["Content-Type: application/json", "X-Mode: dev"]
    
    if data.is_empty():
        http_request.request(url, headers, method)
    else:
        http_request.request(url, headers, method, JSON.stringify(data))
