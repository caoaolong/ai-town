from pydantic import BaseModel, Field

class ContextAgentResponse(BaseModel):
    action_id: str = Field(description="你决定执行的action_id")
    pharse: str = Field(description="一句简单的台词，可自由发挥")