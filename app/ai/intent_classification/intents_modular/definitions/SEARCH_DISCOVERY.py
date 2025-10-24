from ..models import IntentDefinition
from ..enums import IntentCategory, ActionCode, IntentPriority, EntityType

search_discovery_intent_definitions = {
    # 1.1 Product Search Actions
    "search_product": IntentDefinition(
        category=IntentCategory.SEARCH_DISCOVERY,
        action_code=ActionCode.SEARCH_PRODUCT,
        description="User wants to search for specific products",
        example_phrases=[
            "I'm looking for a laptop",
            "Show me smartphones",
            "Find me running shoes",
            "Search for headphones",
            "I need a coffee maker",
            "Looking for winter jackets",
            "Can you find me a camera?",
            "Show me gaming laptops"
        ],
        required_entities=[EntityType.PRODUCT_QUERY],
        optional_entities=[EntityType.CATEGORY, EntityType.BRAND, EntityType.PRICE_RANGE],
        confidence_threshold=0.85,
        priority=IntentPriority.HIGH
    ),

    "search_category": IntentDefinition(
        category=IntentCategory.SEARCH_DISCOVERY,
        action_code=ActionCode.SEARCH_CATEGORY,
        description="User wants to browse products in a specific category",
        example_phrases=[
            "Show me electronics",
            "I want to see clothing",
            "Browse home and garden",
            "Show me sports equipment",
            "I'm looking at books",
            "Display kitchen items",
            "Show me beauty products",
            "I want to see toys"
        ],
        required_entities=[EntityType.CATEGORY],
        optional_entities=[EntityType.PRICE_RANGE, EntityType.BRAND],
        confidence_threshold=0.80,
        priority=IntentPriority.HIGH
    ),

    "search_brand": IntentDefinition(
        category=IntentCategory.SEARCH_DISCOVERY,
        action_code=ActionCode.SEARCH_BRAND,
        description="User wants to find products from a specific brand",
        example_phrases=[
            "Show me Apple products",
            "I want Nike shoes",
            "Find Samsung phones",
            "Show me Adidas clothing",
            "I'm looking for Sony headphones",
            "Display Canon cameras",
            "Show me Toyota cars",
            "I want Levi's jeans"
        ],
        required_entities=[EntityType.BRAND],
        optional_entities=[EntityType.CATEGORY, EntityType.PRICE_RANGE],
        confidence_threshold=0.85,
        priority=IntentPriority.HIGH
    ),

    "search_price_range": IntentDefinition(
        category=IntentCategory.SEARCH_DISCOVERY,
        action_code=ActionCode.SEARCH_PRICE_RANGE,
        description="User wants to find products within a specific price range",
        example_phrases=[
            "Show me laptops under $1000",
            "I want phones between $200 and $500",
            "Find shoes under $50",
            "Show me cameras over $500",
            "I'm looking for watches under $200",
            "Display headphones under $100",
            "Show me tablets between $300 and $600",
            "I want books under $20"
        ],
        required_entities=[EntityType.PRICE_RANGE],
        optional_entities=[EntityType.CATEGORY, EntityType.BRAND],
        confidence_threshold=0.80,
        priority=IntentPriority.HIGH
    ),

    # 1.2 Discovery & Recommendations
    "product_recommendation": IntentDefinition(
        category=IntentCategory.SEARCH_DISCOVERY,
        action_code=ActionCode.PRODUCT_RECOMMENDATION,
        description="User wants product recommendations",
        example_phrases=[
            "What do you recommend?",
            "Give me suggestions",
            "What should I buy?",
            "Show me recommendations",
            "I need recommendations",
            "What would you suggest?",
            "Give me some ideas",
            "What's recommended for me?"
        ],
        required_entities=[],
        optional_entities=[EntityType.CATEGORY, EntityType.BUDGET, EntityType.PREFERENCES],
        confidence_threshold=0.75,
        priority=IntentPriority.HIGH
    ),

    # 1.3 Search Filters & Facets
    "filter_price": IntentDefinition(
        category=IntentCategory.SEARCH_DISCOVERY,
        action_code=ActionCode.FILTER_PRICE,
        description="User wants to filter products by price range",
        example_phrases=[
            "Filter by price",
            "Show me under $100",
            "Filter price range",
            "Between $50 and $200",
            "Under $500",
            "Over $1000",
            "Price filter",
            "Show cheaper options"
        ],
        required_entities=[EntityType.PRICE_RANGE],
        optional_entities=[EntityType.CATEGORY],
        confidence_threshold=0.85,
        priority=IntentPriority.HIGH
    ),

    # 1.4 Sorting & View Options
    "sort_price": IntentDefinition(
        category=IntentCategory.SEARCH_DISCOVERY,
        action_code=ActionCode.SORT_PRICE,
        description="User wants to sort products by price",
        example_phrases=[
            "Sort by price",
            "Order by price",
            "Price low to high",
            "Sort cheapest first",
            "Price high to low",
            "Sort by cost",
            "Order by price range",
            "Sort by price ascending"
        ],
        required_entities=[],
        optional_entities=[EntityType.SORT_CRITERIA],
        confidence_threshold=0.85,
        priority=IntentPriority.MEDIUM
    ),
}