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
            "Buy this now",
            
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

    "empty_cart": IntentDefinition(
        category=IntentCategory.CART_WISHLIST,
        action_code=ActionCode.EMPTY_CART,
        description="User wants to remove all items from their cart",
        example_phrases=[
            "Empty my cart",
            "Clear cart",
            "Remove all items",
            "Empty shopping cart",
            "Clear all items",
            "Remove everything",
            "Empty the cart",
            "Clear my cart"
        ],
        required_entities=[],
        optional_entities=[],
        confidence_threshold=0.85,
        priority=IntentPriority.HIGH
    ),

    "move_to_cart": IntentDefinition(
        category=IntentCategory.CART_WISHLIST,
        action_code=ActionCode.MOVE_TO_CART,
        description="User wants to move an item from wishlist to cart",
        example_phrases=[
            "Move to cart",
            "Add to cart from wishlist",
            "Move this to cart",
            "Buy from wishlist",
            "Add to cart now",
            "Move item to cart",
            "Purchase from wishlist",
            "Add to shopping cart"
        ],
        required_entities=[EntityType.PRODUCT_ID],
        optional_entities=[EntityType.QUANTITY],
        confidence_threshold=0.85,
        priority=IntentPriority.HIGH
    ),

    "save_for_later": IntentDefinition(
        category=IntentCategory.CART_WISHLIST,
        action_code=ActionCode.SAVE_FOR_LATER,
        description="User wants to save a cart item for later purchase",
        example_phrases=[
            "Save for later",
            "Keep for later",
            "Save this item",
            "Put aside for later",
            "Save for future",
            "Keep this for later",
            "Save item",
            "Hold for later"
        ],
        required_entities=[EntityType.PRODUCT_ID],
        optional_entities=[],
        confidence_threshold=0.80,
        priority=IntentPriority.MEDIUM
    ),

    "cart_total": IntentDefinition(
        category=IntentCategory.CART_WISHLIST,
        action_code=ActionCode.CART_TOTAL,
        description="User wants to know the total cost of their cart",
        example_phrases=[
            "What's my total?",
            "Show cart total",
            "How much is everything?",
            "Total cost",
            "What's the total?",
            "Show me total",
            "Cart total",
            "How much do I owe?"
        ],
        required_entities=[],
        optional_entities=[],
        confidence_threshold=0.90,
        priority=IntentPriority.HIGH
    ),

    "cart_item_details": IntentDefinition(
        category=IntentCategory.CART_WISHLIST,
        action_code=ActionCode.CART_ITEM_DETAILS,
        description="User wants to see details of a specific cart item",
        example_phrases=[
            "Show item details",
            "Tell me about this item",
            "Item information",
            "Show details",
            "What is this item?",
            "Item specs",
            "Show me details",
            "Product details"
        ],
        required_entities=[EntityType.PRODUCT_ID],
        optional_entities=[],
        confidence_threshold=0.80,
        priority=IntentPriority.MEDIUM
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

    "remove_coupon": IntentDefinition(
        category=IntentCategory.CART_WISHLIST,
        action_code=ActionCode.REMOVE_COUPON,
        description="User wants to remove a coupon from their cart",
        example_phrases=[
            "Remove coupon",
            "Remove discount",
            "Take off coupon",
            "Remove promo code",
            "Remove code",
            "Cancel coupon",
            "Remove discount code",
            "Take off discount"
        ],
        required_entities=[EntityType.COUPON_CODE],
        optional_entities=[],
        confidence_threshold=0.85,
        priority=IntentPriority.MEDIUM
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

    "view_recently_viewed": IntentDefinition(
        category=IntentCategory.CART_WISHLIST,
        action_code=ActionCode.VIEW_RECENTLY_VIEWED,
        description="User wants to see recently viewed products",
        example_phrases=[
            "Show recently viewed",
            "What did I look at?",
            "Recently viewed items",
            "Show my history",
            "What I viewed recently",
            "Recent products",
            "Show me recent items",
            "Viewing history"
        ],
        required_entities=[],
        optional_entities=[],
        confidence_threshold=0.80,
        priority=IntentPriority.MEDIUM
    ),

    "clear_recently_viewed": IntentDefinition(
        category=IntentCategory.CART_WISHLIST,
        action_code=ActionCode.CLEAR_RECENTLY_VIEWED,
        description="User wants to clear their recently viewed history",
        example_phrases=[
            "Clear recently viewed",
            "Clear my history",
            "Remove recent items",
            "Clear viewing history",
            "Delete recent items",
            "Clear history",
            "Remove recent views",
            "Clear my recent items"
        ],
        required_entities=[],
        optional_entities=[],
        confidence_threshold=0.80,
        priority=IntentPriority.LOW
    ),

    "move_to_wishlist": IntentDefinition(
        category=IntentCategory.CART_WISHLIST,
        action_code=ActionCode.MOVE_TO_WISHLIST,
        description="User wants to move an item from cart to wishlist",
        example_phrases=[
            "Move to wishlist",
            "Save for later",
            "Move to saved items",
            "Add to wishlist",
            "Save to wishlist",
            "Move item to wishlist",
            "Put in wishlist",
            "Save this for later"
        ],
        required_entities=[EntityType.PRODUCT_ID],
        optional_entities=[],
        confidence_threshold=0.85,
        priority=IntentPriority.MEDIUM
    ),

    "gift_wrap": IntentDefinition(
        category=IntentCategory.CART_WISHLIST,
        action_code=ActionCode.GIFT_WRAP,
        description="User wants to add gift wrapping to an item",
        example_phrases=[
            "Add gift wrap",
            "I want gift wrapping",
            "Wrap as gift",
            "Add gift packaging",
            "Gift wrap this",
            "Wrap for gift",
            "Add wrapping",
            "Make it a gift"
        ],
        required_entities=[EntityType.PRODUCT_ID],
        optional_entities=[],
        confidence_threshold=0.85,
        priority=IntentPriority.MEDIUM
    ),

    "add_note": IntentDefinition(
        category=IntentCategory.CART_WISHLIST,
        action_code=ActionCode.ADD_NOTE,
        description="User wants to add a note to a cart item",
        example_phrases=[
            "Add a note",
            "I want to add a note",
            "Add special instructions",
            "Add message",
            "Add comment",
            "Add note to item",
            "Special instructions",
            "Add note to order"
        ],
        required_entities=[EntityType.PRODUCT_ID],
        optional_entities=[],
        confidence_threshold=0.80,
        priority=IntentPriority.LOW
    ),
}