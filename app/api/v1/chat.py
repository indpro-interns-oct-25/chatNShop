from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.product import ProductSchema
from app.services.qdrant_service import qdrant_service
from app.services.product_service import product_service
from app.ai.intent_classification.rule_based import get_intent_rule_based

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def handle_chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    # 1. Classify Intent
    intent = get_intent_rule_based(request.query)

    # 2. Handle based on intent
    if intent == "search_product":
        try:
            # A. Find similar products in Qdrant
            search_results = qdrant_service.search(request.query)

            # B. Get the full product details from PostgreSQL
            product_ids = [r.payload['sql_id'] for r in search_results if 'sql_id' in r.payload]
            products = product_service.get_products_by_ids(db, product_ids)

            # C. Convert to Pydantic schemas for the response
            product_schemas = [ProductSchema.model_validate(p) for p in products]

            return ChatResponse(
                response_type="products",
                data=product_schemas
            )
        except Exception as e:
            return ChatResponse(response_type="error", data=str(e))

    elif intent == "order_status":
        # (In a real app, you would look up the order status)
        return ChatResponse(
            response_type="text",
            data="Your order #12345 is out for delivery and should arrive today."
        )

    elif intent == "add_to_cart":
        # (In a real app, you would add an item to the user's cart)
        return ChatResponse(
            response_type="text",
            data="Added 'Classic Cotton T-Shirt' to your cart!"
        )

    else:
        return ChatResponse(
            response_type="text",
            data="I'm sorry, I didn't understand that. Can you try rephrasing?"
        )