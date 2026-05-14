from pydantic import BaseModel, Field

class AITodoListResponse(BaseModel):
    todo_list: list["AITodoItem"] = Field(description="你今天要执行的todo列表，按照优先级排序")

class AITodoItem(BaseModel):
    action_id: str = Field(description="你决定执行的action_id")
    action_label: str = Field(description="你决定执行的action_label")
    action_description: str = Field(description="一句简单的描述，用于突出人物特点")
    action_percent: float = Field(description="你决定执行的action_id的在今天的占比，范围0-1，所有TodoItem的action_percent总和要等于1")