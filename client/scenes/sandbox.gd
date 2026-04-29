extends Control

var ws_client: WebSocketPeer

# Called when the node enters the scene tree for the first time.
func _ready() -> void:
    ws_client = WebSocketPeer.new()
    var err = ws_client.connect_to_url(Config.WS_BASE_URL)
    if err != OK:
        print("WebSocket connection error: ", err)

func _process(_delta: float) -> void:
    ws_client.poll()
    var state = ws_client.get_ready_state()
    if state == WebSocketPeer.STATE_OPEN:
        while ws_client.get_available_packet_count() > 0:
            var msg = ws_client.get_packet().get_string_from_utf8()
            print("收到消息: ", msg)