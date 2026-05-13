class_name Schema

class Context:
    var action_id: String = ""
    var direction: String = ""
    var pharse: String = ""
    func _init() -> void:
        pass
    
    func from_dict(dict: Dictionary) -> Context:
        self.action_id = dict.get("action_id", "")
        self.direction = dict.get("direction", "")
        self.pharse = dict.get("pharse", "")
        return self