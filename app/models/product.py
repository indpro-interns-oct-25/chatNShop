from sqlalchemy import Column, Integer, String, Float, Text
from app.core.db import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    price = Column(Float)
    category = Column(String, index=True, nullable=True)
    image_url = Column(String, nullable=True)