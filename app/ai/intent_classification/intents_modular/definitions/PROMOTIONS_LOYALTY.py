from ..models import IntentDefinition
from ..enums import IntentCategory, ActionCode, IntentPriority, EntityType

promotions_loyalty_intent_definitions = {
    # 8.0 Promotions, Offers & Loyalty
    "view_promotions": IntentDefinition(
        category=IntentCategory.PROMOTIONS_LOYALTY,
        action_code=ActionCode.VIEW_PROMOTIONS,
        description="User wants to see current promotions and offers",
        example_phrases=[
            "Show me promotions",
            "What promotions are available?",
            "Current promotions",
            "Show promotions",
            "Available offers",
            "What deals are there?",
            "Promotional offers",
            "Show me deals"
        ],
        required_entities=[],
        optional_entities=[EntityType.CATEGORY],
        confidence_threshold=0.85,
        priority=IntentPriority.HIGH
    ),

    "view_coupons": IntentDefinition(
        category=IntentCategory.PROMOTIONS_LOYALTY,
        action_code=ActionCode.VIEW_COUPONS,
        description="User wants to see available coupons",
        example_phrases=[
            "Show me coupons",
            "Available coupons",
            "What coupons do I have?",
            "Show coupons",
            "My coupons",
            "Coupon codes",
            "Available discount codes",
            "Show discount codes"
        ],
        required_entities=[],
        optional_entities=[],
        confidence_threshold=0.85,
        priority=IntentPriority.HIGH
    ),

    "apply_promo": IntentDefinition(
        category=IntentCategory.PROMOTIONS_LOYALTY,
        action_code=ActionCode.APPLY_PROMO,
        description="User wants to apply a promotional offer",
        example_phrases=[
            "Apply promotion",
            "Use this promotion",
            "Apply promo code",
            "Use promotional offer",
            "Apply deal",
            "Use this deal",
            "Apply offer",
            "Use promotion"
        ],
        required_entities=[],
        optional_entities=[EntityType.COUPON_CODE],
        confidence_threshold=0.85,
        priority=IntentPriority.HIGH
    ),

    "view_sale_collection": IntentDefinition(
        category=IntentCategory.PROMOTIONS_LOYALTY,
        action_code=ActionCode.VIEW_SALE_COLLECTION,
        description="User wants to see products on sale",
        example_phrases=[
            "Show me sale items",
            "What's on sale?",
            "Sale collection",
            "Items on sale",
            "Show sales",
            "Discounted items",
            "Sale products",
            "Show me deals"
        ],
        required_entities=[],
        optional_entities=[EntityType.CATEGORY, EntityType.PRICE_RANGE],
        confidence_threshold=0.85,
        priority=IntentPriority.HIGH
    ),
}