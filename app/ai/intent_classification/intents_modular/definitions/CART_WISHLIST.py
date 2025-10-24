from ..models import IntentDefinition
from ..enums import IntentCategory, ActionCode, IntentPriority, EntityType

cart_wishlist_intent_definitions = {
    # 3.0 Cart & Wishlist Management
    "add_to_cart": IntentDefinition(
        category=IntentCategory.CART_WISHLIST,
        action_code=ActionCode.ADD_TO_CART,
        description="User wants to add a product to their shopping cart",
        example_phrases=[
            "Add to cart",
            "I want to buy this",
            "Add this to my cart",
            "Put this in my cart",
            "Add to shopping cart",
            "I'll take this",
            "Add this item",
            "Buy this now"
        ],
        required_entities=[EntityType.PRODUCT_ID],
        optional_entities=[EntityType.QUANTITY, EntityType.SIZE, EntityType.COLOR],
        confidence_threshold=0.90,
        priority=IntentPriority.HIGH
    ),

    "remove_from_cart": IntentDefinition(
        category=IntentCategory.CART_WISHLIST,
        action_code=ActionCode.REMOVE_FROM_CART,
        description="User wants to remove a product from their shopping cart",
        example_phrases=[
            "Remove from cart",
            "Take this out",
            "Remove this item",
            "Delete from cart",
            "Remove this product",
            "Take out of cart",
            "Remove item",
            "Delete this"
        ],
        required_entities=[EntityType.PRODUCT_ID],
        optional_entities=[],
        confidence_threshold=0.90,
        priority=IntentPriority.HIGH
    ),

    "update_cart_quantity": IntentDefinition(
        category=IntentCategory.CART_WISHLIST,
        action_code=ActionCode.UPDATE_CART_QUANTITY,
        description="User wants to change the quantity of an item in their cart",
        example_phrases=[
            "Change quantity to 3",
            "Update quantity",
            "I want 2 of these",
            "Change to 5",
            "Update the amount",
            "Set quantity to 1",
            "Change number to 4",
            "Update how many"
        ],
        required_entities=[EntityType.PRODUCT_ID, EntityType.QUANTITY],
        optional_entities=[],
        confidence_threshold=0.85,
        priority=IntentPriority.HIGH
    ),

    "view_cart": IntentDefinition(
        category=IntentCategory.CART_WISHLIST,
        action_code=ActionCode.VIEW_CART,
        description="User wants to see their shopping cart",
        example_phrases=[
            "Show my cart",
            "View cart",
            "See my cart",
            "Show shopping cart",
            "Display cart",
            "I want to see my cart",
            "Show me cart",
            "View my items"
        ],
        required_entities=[],
        optional_entities=[],
        confidence_threshold=0.90,
        priority=IntentPriority.HIGH
    ),

    "add_to_wishlist": IntentDefinition(
        category=IntentCategory.CART_WISHLIST,
        action_code=ActionCode.ADD_TO_WISHLIST,
        description="User wants to add a product to their wishlist",
        example_phrases=[
            "Add to wishlist",
            "Save to wishlist",
            "Add to favorites",
            "Save for later",
            "Add to saved items",
            "Wishlist this",
            "Save this item",
            "Add to my list"
        ],
        required_entities=[EntityType.PRODUCT_ID],
        optional_entities=[],
        confidence_threshold=0.90,
        priority=IntentPriority.HIGH
    ),

    "remove_from_wishlist": IntentDefinition(
        category=IntentCategory.CART_WISHLIST,
        action_code=ActionCode.REMOVE_FROM_WISHLIST,
        description="User wants to remove a product from their wishlist",
        example_phrases=[
            "Remove from wishlist",
            "Delete from wishlist",
            "Remove from favorites",
            "Take off wishlist",
            "Remove from saved",
            "Delete from saved",
            "Remove this item",
            "Take off my list"
        ],
        required_entities=[EntityType.PRODUCT_ID],
        optional_entities=[],
        confidence_threshold=0.90,
        priority=IntentPriority.HIGH
    ),

    "view_wishlist": IntentDefinition(
        category=IntentCategory.CART_WISHLIST,
        action_code=ActionCode.VIEW_WISHLIST,
        description="User wants to see their wishlist",
        example_phrases=[
            "Show my wishlist",
            "View wishlist",
            "See my wishlist",
            "Show saved items",
            "Display wishlist",
            "I want to see my wishlist",
            "Show me wishlist",
            "View saved items"
        ],
        required_entities=[],
        optional_entities=[],
        confidence_threshold=0.90,
        priority=IntentPriority.HIGH
    ),

    "apply_coupon": IntentDefinition(
        category=IntentCategory.CART_WISHLIST,
        action_code=ActionCode.APPLY_COUPON,
        description="User wants to apply a coupon code to their cart",
        example_phrases=[
            "Apply coupon",
            "Use this code",
            "Apply discount code",
            "Use coupon code",
            "Apply promo code",
            "Use this coupon",
            "Apply code",
            "Use discount"
        ],
        required_entities=[EntityType.COUPON_CODE],
        optional_entities=[],
        confidence_threshold=0.90,
        priority=IntentPriority.HIGH
    ),
}