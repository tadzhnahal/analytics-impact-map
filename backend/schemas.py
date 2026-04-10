from pydantic import BaseModel, Field

class ComponentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    component_type: str = Field(min_length=1, max_length=50)
    description: str | None = None

class ComponentOut(BaseModel):
    id: int
    name: str
    component_type: str
    description: str | None = None