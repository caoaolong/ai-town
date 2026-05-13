extends CharacterBody2D

class_name AgentPlayer

## 头像
@export var avatar: AtlasTexture
@export var speed: float = 40.0
@export var tilemap: TileMapLayer

@onready var animated_sprite: AnimatedSprite2D = $AnimatedSprite2D
@onready var arrow: Sprite2D = $Arrow
@onready var animation_player: AnimationPlayer = $AnimationPlayer

var astar: AStarGrid2D = AStarGrid2D.new()
# 添加 HTTPRequest 节点引用
var http_request: HTTPRequest = HTTPRequest.new()
var current_state: Dictionary = {}
var DIRECTION_VECTORS = {
    Config.NORTH: Vector2i(0, -1),
    Config.SOUTH: Vector2i(0, 1),
    Config.EAST: Vector2i(1, 0),
    Config.WEST: Vector2i(-1, 0),
    Config.NORTH_EAST: Vector2i(1, -1),
    Config.NORTH_WEST: Vector2i(-1, -1),
    Config.SOUTH_EAST: Vector2i(1, 1),
    Config.SOUTH_WEST: Vector2i(-1, 1)
}

var current_path = []
var path_index = 0

func _ready() -> void:
    _build_astar()
    _init_http_request()
    
    move_to(Vector2(-144, 40))

func _process(_delta: float) -> void:
    if path_index >= current_path.size():
        velocity = Vector2.ZERO
        move_and_slide()
        return
    var target_cell = current_path[path_index]
    var target_world = tilemap.to_global(tilemap.map_to_local(target_cell))
    var dir = target_world - global_position
    if dir.length() < 2:
        path_index += 1
    else:
        velocity = dir.normalized() * speed
    move_and_slide()


func _build_astar():
    astar.region = tilemap.get_used_rect()
    astar.cell_size = Vector2(tilemap.tile_set.tile_size)
    astar.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_NEVER
    astar.update()
    for cell in tilemap.get_used_cells():
        var tile_data = tilemap.get_cell_tile_data(cell)
        if tile_data == null:
            continue
        astar.set_point_solid(cell, _tile_blocks_pathfinding(tile_data))


func move_to(target_world_pos: Vector2):
    var start_cell = tilemap.local_to_map(tilemap.to_local(global_position))

    var end_cell = tilemap.local_to_map(tilemap.to_local(target_world_pos))

    current_path = astar.get_id_path(start_cell, end_cell)

    path_index = 0


func _tile_blocks_pathfinding(tile_data: TileData) -> bool:
    if tile_data.get_custom_data("is_walkable") == true:
        return false
    var type_name = tile_data.get_custom_data("type_name")
    if type_name is String and not type_name.is_empty():
        return true
    return tile_data.get_collision_polygons_count(0) > 0


func show_arrow() -> void:
    animation_player.play("focus")
    arrow.visible = true

func hide_arrow() -> void:
    animation_player.stop()
    arrow.visible = false


## 初始化 HTTP 请求节点
func _init_http_request() -> void:
    add_child(http_request)
    http_request.request_completed.connect(_on_http_request_completed)


## 处理 HTTP 请求完成
func _on_http_request_completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
    if result == HTTPRequest.RESULT_SUCCESS and response_code == 200:
        var response = JSON.parse_string(body.get_string_from_utf8())
        match response["event_type"]:
            Config.EV_CONTEXT:
                var context = Schema.Context.new().from_dict(response["data"])
                print(context)
    else:
        print("[AgentPlayer] HTTP Request Failed. Error: ", result)


## 发送 HTTP 请求
func _send_http_request(endpoint: String, method: HTTPClient.Method=HTTPClient.METHOD_GET, data: Dictionary = {}) -> void:
    var url = Config.HTTP_BASE_URL + endpoint
    var headers = ["Content-Type: application/json"]
    
    if data.is_empty():
        http_request.request(url, headers, method)
    else:
        http_request.request(url, headers, method, JSON.stringify(data))


## 发送状态（用于角色碰撞等事件，后续可扩展）
func send_state(event_type: String, data: Dictionary) -> void:
    _send_http_request("/state", HTTPClient.METHOD_POST, {
        "player": name,
        "event_type": event_type,
        "data": data
    })
