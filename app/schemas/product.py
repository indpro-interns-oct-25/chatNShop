from pydantic import BaseModel, ConfigDict
from typing import Optional

class ProductSchema(BaseModel):
    # This tells Pydantic to allow reading from ORM models
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    price: float
    category: Optional[str] = None
    image_url: Optional[str] = None