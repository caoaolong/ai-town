extends GridContainer

class_name TodoListView

const _TODO_FONT := preload("res://resources/fonts/aitown.ttf")
const _TODO_HEADER_CELL_COUNT := 4


func _ready() -> void:
    GM.todo_list_received.connect(populate_todo_list_panel)


func populate_todo_list_panel(payload: Dictionary) -> void:
    var inner = payload.get("data")
    if inner == null or not (inner is Dictionary):
        return
    var todo_arr = (inner as Dictionary).get("todo_list")
    if todo_arr == null or not (todo_arr is Array):
        return
    _clear_todo_list_dynamic_rows()
    for item in todo_arr as Array:
        if not (item is Dictionary):
            continue
        var d := item as Dictionary
        var action_label = str(d.get("action_label", ""))
        var action_description = str(d.get("action_description", ""))
        var action_percent = float(d.get("action_percent", 0.0))
        var state_lbl := Label.new()
        state_lbl.text = "—"
        state_lbl.add_theme_font_override(&"font", _TODO_FONT)
        state_lbl.add_theme_font_size_override(&"font_size", 14)
        add_child(state_lbl)
        var bar := ProgressBar.new()
        bar.min_value = 0.0
        bar.max_value = 100.0
        bar.value = action_percent
        bar.show_percentage = false
        bar.custom_minimum_size = Vector2(64.0, 18.0)
        add_child(bar)
        var pct_lbl := Label.new()
        pct_lbl.text = "%.0f%%" % action_percent
        pct_lbl.add_theme_font_override(&"font", _TODO_FONT)
        pct_lbl.add_theme_font_size_override(&"font_size", 14)
        add_child(pct_lbl)
        var thing_lbl := Label.new()
        thing_lbl.text = action_label
        thing_lbl.tooltip_text = action_description
        thing_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
        thing_lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
        thing_lbl.add_theme_font_override(&"font", _TODO_FONT)
        thing_lbl.add_theme_font_size_override(&"font_size", 14)
        add_child(thing_lbl)


func _clear_todo_list_dynamic_rows() -> void:
    while get_child_count() > _TODO_HEADER_CELL_COUNT:
        var last = get_child(get_child_count() - 1)
        remove_child(last)
        last.queue_free()
