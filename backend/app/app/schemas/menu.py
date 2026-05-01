from pydantic import BaseModel, ConfigDict, Field


class MenuOptionChoice(BaseModel):
    id: str
    name: str
    price_delta: int = 0
    is_available: bool = True


class MenuOptionGroup(BaseModel):
    id: str
    name: str
    required: bool
    min_select: int = Field(ge=0)
    max_select: int = Field(ge=0)
    choices: list[MenuOptionChoice]


class MenuItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    brand_id: str | None = None
    name: str
    category: str
    description: str | None = None
    price: int
    image_url: str | None = None
    is_available: bool
    ingredients: list[str] = Field(default_factory=list)
    options: list[MenuOptionGroup] = Field(default_factory=list)
