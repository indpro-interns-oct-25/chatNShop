from sqlalchemy.orm import Session
from typing import List
from app.models.product import Product

class ProductService:
    def get_products_by_ids(self, db: Session, product_ids: List[int]) -> List[Product]:
        if not product_ids:
            return []
        return db.query(Product).filter(Product.id.in_(product_ids)).all()

# Create a single, reusable instance
product_service = ProductService()