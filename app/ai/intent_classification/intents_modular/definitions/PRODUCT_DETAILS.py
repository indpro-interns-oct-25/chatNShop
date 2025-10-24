from ..models import IntentDefinition
from ..enums import IntentCategory, ActionCode, IntentPriority, EntityType

product_details_intent_definitions = {
    # 2.0 Product Details & Information
    "product_info": IntentDefinition(
        category=IntentCategory.PRODUCT_DETAILS,
        action_code=ActionCode.PRODUCT_INFO,
        description="User wants general information about a product",
        example_phrases=[
            "Tell me about this product",
            "What is this?",
            "Product information",
            "Show me details",
            "What does this do?",
            "Tell me more",
            "Product specs",
            "What's this product about?"
        ],
        required_entities=[EntityType.PRODUCT_ID],
        optional_entities=[],
        confidence_threshold=0.85,
        priority=IntentPriority.HIGH
    ),

    "product_details": IntentDefinition(
        category=IntentCategory.PRODUCT_DETAILS,
        action_code=ActionCode.PRODUCT_DETAILS,
        description="User wants detailed information about a specific product",
        example_phrases=[
            "Show me product details",
            "I want to see details",
            "Product specifications",
            "Show full details",
            "Detailed information",
            "Complete product info",
            "Show me everything",
            "Full product details"
        ],
        required_entities=[EntityType.PRODUCT_ID],
        optional_entities=[],
        confidence_threshold=0.85,
        priority=IntentPriority.HIGH
    ),

    "product_availability": IntentDefinition(
        category=IntentCategory.PRODUCT_DETAILS,
        action_code=ActionCode.PRODUCT_AVAILABILITY,
        description="User wants to check if a product is available",
        example_phrases=[
            "Is this available?",
            "Check availability",
            "Is it in stock?",
            "Can I buy this?",
            "Is this product available?",
            "Stock status",
            "Is it available now?",
            "Check if in stock"
        ],
        required_entities=[EntityType.PRODUCT_ID],
        optional_entities=[],
        confidence_threshold=0.85,
        priority=IntentPriority.HIGH
    ),

    "product_price": IntentDefinition(
        category=IntentCategory.PRODUCT_DETAILS,
        action_code=ActionCode.PRODUCT_PRICE,
        description="User wants to know the price of a product",
        example_phrases=[
            "How much is this?",
            "What's the price?",
            "Show me the price",
            "How much does it cost?",
            "Price information",
            "What's the cost?",
            "Show price",
            "How much?"
        ],
        required_entities=[EntityType.PRODUCT_ID],
        optional_entities=[],
        confidence_threshold=0.90,
        priority=IntentPriority.HIGH
    ),

    "product_variants": IntentDefinition(
        category=IntentCategory.PRODUCT_DETAILS,
        action_code=ActionCode.PRODUCT_VARIANTS,
        description="User wants to see all available variants of a product",
        example_phrases=[
            "Show me all variants",
            "What variants are available?",
            "Show product variants",
            "Available options",
            "Show me options",
            "What options are there?",
            "Product variations",
            "Show all options"
        ],
        required_entities=[EntityType.PRODUCT_ID],
        optional_entities=[],
        confidence_threshold=0.80,
        priority=IntentPriority.HIGH
    ),

    "product_reviews": IntentDefinition(
        category=IntentCategory.PRODUCT_DETAILS,
        action_code=ActionCode.PRODUCT_REVIEWS,
        description="User wants to see product reviews",
        example_phrases=[
            "Show me reviews",
            "I want to see reviews",
            "Product reviews",
            "Show reviews",
            "Customer reviews",
            "What do people say?",
            "Show me feedback",
            "User reviews"
        ],
        required_entities=[EntityType.PRODUCT_ID],
        optional_entities=[],
        confidence_threshold=0.85,
        priority=IntentPriority.HIGH
    ),
}