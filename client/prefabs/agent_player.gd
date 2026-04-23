extends CharacterBody2D

class_name AgentPlayer

## 头像
@export var avatar: AtlasTexture
## 移动速度
@export var speed: float = 50.0
## 方向改变的最小时间间隔（秒）
@export var min_change_direction_time: float = 1.0
## 方向改变的最大时间间隔（秒）
@export var max_change_direction_time: float = 3.0

@onready var animated_sprite: AnimatedSprite2D = $AnimatedSprite2D
# 添加 HTTPRequest 节点引用
var http_request: HTTPRequest

# 四个方向：上、下、左、右（只能是纯方向，不能混合）
enum Direction {UP, DOWN, LEFT, RIGHT}
var _current_direction: Direction = Direction.DOWN
var _change_direction_timer: float = 0.0

# 方向对应的动画名称
const DIRECTION_ANIMATIONS = {
    Direction.UP: "run_backward",
    Direction.DOWN: "run_forward",
    Direction.LEFT: "run_left",
    Direction.RIGHT: "run_right"
}

# 方向对应的速度向量
const DIRECTION_VELOCITIES = {
    Direction.UP: Vector2(0, -1),
    Direction.DOWN: Vector2(0, 1),
    Direction.LEFT: Vector2(-1, 0),
    Direction.RIGHT: Vector2(1, 0)
}

# 相反方向映射
const OPPOSITE_DIRECTIONS = {
    Direction.UP: Direction.DOWN,
    Direction.DOWN: Direction.UP,
    Direction.LEFT: Direction.RIGHT,
    Direction.RIGHT: Direction.LEFT
}

# 全部轴向（用于随机换向，避免依赖枚举反射）
const ALL_DIRECTIONS: Array[Direction] = [
    Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT,
]

# 添加基础 URL 常量
const BASE_URL = "http://127.0.0.1:5000"


func _ready() -> void:
    _set_random_direction()
    # 初始化 HTTPRequest 节点
    _init_http_request()


func _physics_process(delta: float) -> void:
    # 更新计时器，定期改变方向
    _change_direction_timer -= delta
    if _change_direction_timer <= 0.0:
        _set_random_direction()

    # 设置速度并移动
    velocity = DIRECTION_VELOCITIES[_current_direction] * speed
    move_and_slide()

    # 播放对应的动画
    var anim_name: String = DIRECTION_ANIMATIONS[_current_direction]
    if animated_sprite.animation != anim_name:
        animated_sprite.play(anim_name)

    # 碰撞检测
    if get_slide_collision_count() > 0:
        _handle_collision()


## 处理碰撞逻辑
func _handle_collision() -> void:
    for i in range(get_slide_collision_count()):
        var collider = get_slide_collision(i).get_collider()
        if collider == null or not collider is Node:
            continue
        var n: Node = collider

        # 检查碰撞对象是否在 world_wall 组
        if n.is_in_group("world_wall"):
            # 产生相反方向（仅墙体允许反向），方向必然改变，重置随机换向计时器
            _current_direction = OPPOSITE_DIRECTIONS[_current_direction]
            _arm_direction_timer()
            return

        # 检查碰撞对象是否在 player 组
        if n.is_in_group("player"):
            send_event("player_meet", n)
            return

        if n.is_in_group("plant"):
            _set_random_direction(true)
            return


## 随机方向（永不取当前反方向）。reset_timer：非碰撞路径为 true
func _set_random_direction(reset_timer: bool = true) -> void:
    var opp: Direction = OPPOSITE_DIRECTIONS[_current_direction]
    var pick: int = randi() % 3
    for dir in ALL_DIRECTIONS:
        if dir == opp:
            continue
        if pick == 0:
            _current_direction = dir
            break
        pick -= 1
    if reset_timer:
        _arm_direction_timer()


func _arm_direction_timer() -> void:
    _change_direction_timer = randf_range(min_change_direction_time, max_change_direction_time)


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
## endpoint: 请求的接口路径
## method: HTTP 方法 (GET, POST, etc.)
## data: 请求体数据 (可选)
func _send_http_request(endpoint: String, method: HTTPClient.Method=HTTPClient.METHOD_GET, data: String = "") -> void:
    var url = BASE_URL + endpoint
    var headers = ["Content-Type: application/json"]
    
    if data.is_empty():
        http_request.request(url, headers, method)
    else:
        http_request.request(url, headers, method, data)


## 发送事件（用于角色碰撞等事件，后续可扩展）
## event_type: 事件类型
## other: 事件相关的其他对象（如碰撞的另一个角色）
func send_event(event_type: String, other: Node = null) -> void:
    print("[AgentPlayer] Event: %s, Other: %s" % [event_type, other])
    
    # 测试健康检查接口
    # _send_http_request("/health", HTTPClient.METHOD_GET)
