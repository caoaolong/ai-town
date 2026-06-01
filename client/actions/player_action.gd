class_name PlayerAction

var action_map = {
    "work_to_chop": self.working,
    "work_to_feed": self.working,
    "work_to_plant": self.working,
    "work_to_sell": self.working,
    "chop_to_save": self.chop,
}

func working() -> void:
    pass

func chop() -> void:
    pass