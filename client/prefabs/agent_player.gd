extends CharacterBody2D

class_name AgentPlayer

## 头像
@export var avatar: AtlasTexture
@onready var animated_sprite: AnimatedSprite2D = $AnimatedSprite2D
# 添加 HTTPRequest 节点引用
var http_request: HTTPRequest
var tilemaps: Array[Node] = []

func _ready() -> void:
    _init_http_request()
    tilemaps = get_node("../../Scene").get_children() as Array[Node]


func create_state() -> Dictionary:
    var result: Dictionary = {
        "north": [],
        "south": [],
        "east": [],
        "west": [],
        "north_east": [],
        "north_west": [],
        "south_east": [],
        "south_west": []
    }
    var background_tilemap = tilemaps[0] as TileMapLayer
    var center_cell = background_tilemap.local_to_map(background_tilemap.to_local(global_position))
    var total = 0
    for i in range(1, tilemaps.size()):
        var tilemap = tilemaps[i] as TileMapLayer
        # 北方
        _map_tile(result["north"], tilemap, Vector2i(center_cell.x, center_cell.y - 1))
        total += result["north"].size()
        # 南方
        _map_tile(result["south"], tilemap, Vector2i(center_cell.x, center_cell.y + 1))
        total += result["south"].size()
        # 东方
        _map_tile(result["east"], tilemap, Vector2i(center_cell.x + 1, center_cell.y))
        total += result["east"].size()
        # 西方
        _map_tile(result["west"], tilemap, Vector2i(center_cell.x - 1, center_cell.y))
        total += result["west"].size()
        # 东北方
        _map_tile(result["north_east"], tilemap, Vector2i(center_cell.x + 1, center_cell.y - 1))
        total += result["north_east"].size()
        # 西北方
        _map_tile(result["north_west"], tilemap, Vector2i(center_cell.x - 1, center_cell.y - 1))
        total += result["north_west"].size()
        # 东南方
        _map_tile(result["south_east"], tilemap, Vector2i(center_cell.x + 1, center_cell.y + 1))
        total += result["south_east"].size()
        # 西南方
        _map_tile(result["south_west"], tilemap, Vector2i(center_cell.x - 1, center_cell.y + 1))
        total += result["south_west"].size()
    return {
        "total": total,
        "details": result
    }


func _map_tile(tiles: Array, tilemap: TileMapLayer, _position: Vector2i) -> void:
    var tile = tilemap.get_cell_tile_data(_position)
    if tile == null:
        return
    tiles.append(tile.get_custom_data("type_name"))


## 初始化 HTTP 请求节点
func _init_http_request() -> void:
    http_request = HTTPRequest.new()
    add_child(http_request)
    http_request.request_completed.connect(_on_http_request_completed)


## 处理 HTTP 请求完成
func _on_http_request_completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
    if result == HTTPRequest.RESULT_SUCCESS:
        print("[AgentPlayer] HTTP Request Successful. Response Code: ", response_code)
        print("[AgentPlayer] Response Body: ", body.get_string_from_utf8())
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
