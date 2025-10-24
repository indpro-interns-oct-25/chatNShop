from ..models import IntentDefinition
from ..enums import IntentCategory, ActionCode, IntentPriority, EntityType

orders_fulfillment_intent_definitions = {
    # 5.0 Orders & Fulfillment
    "order_status": IntentDefinition(
        category=IntentCategory.ORDERS_FULFILLMENT,
        action_code=ActionCode.ORDER_STATUS,
        description="User wants to check the status of their order",
        example_phrases=[
            "What's my order status?",
            "Check order status",
            "Order status",
            "Where is my order?",
            "Status of my order",
            "How is my order?",
            "Order progress",
            "Check my order"
        ],
        required_entities=[EntityType.ORDER_ID],
        optional_entities=[],
        confidence_threshold=0.90,
        priority=IntentPriority.HIGH
    ),

    "order_history": IntentDefinition(
        category=IntentCategory.ORDERS_FULFILLMENT,
        action_code=ActionCode.ORDER_HISTORY,
        description="User wants to see their order history",
        example_phrases=[
            "Show my order history",
            "Order history",
            "My past orders",
            "Previous orders",
            "Show order history",
            "All my orders",
            "Order list",
            "Past purchases"
        ],
        required_entities=[],
        optional_entities=[EntityType.DATE_RANGE],
        confidence_threshold=0.90,
        priority=IntentPriority.HIGH
    ),

    "order_cancel": IntentDefinition(
        category=IntentCategory.ORDERS_FULFILLMENT,
        action_code=ActionCode.ORDER_CANCEL,
        description="User wants to cancel their order",
        example_phrases=[
            "Cancel my order",
            "I want to cancel",
            "Cancel order",
            "Cancel this order",
            "I need to cancel",
            "Cancel purchase",
            "Cancel my purchase",
            "Stop this order"
        ],
        required_entities=[EntityType.ORDER_ID],
        optional_entities=[EntityType.REASON],
        confidence_threshold=0.90,
        priority=IntentPriority.CRITICAL
    ),

    "track_shipment": IntentDefinition(
        category=IntentCategory.ORDERS_FULFILLMENT,
        action_code=ActionCode.TRACK_SHIPMENT,
        description="User wants to track their shipment",
        example_phrases=[
            "Track my package",
            "Where is my package?",
            "Track shipment",
            "Package tracking",
            "Track delivery",
            "Where's my delivery?",
            "Track my order",
            "Package status"
        ],
        required_entities=[EntityType.ORDER_ID],
        optional_entities=[],
        confidence_threshold=0.90,
        priority=IntentPriority.HIGH
    ),

    "reorder": IntentDefinition(
        category=IntentCategory.ORDERS_FULFILLMENT,
        action_code=ActionCode.REORDER,
        description="User wants to reorder a previous purchase",
        example_phrases=[
            "Reorder this",
            "I want to reorder",
            "Order again",
            "Buy again",
            "Reorder item",
            "Purchase again",
            "Order same thing",
            "Buy this again"
        ],
        required_entities=[EntityType.ORDER_ID],
        optional_entities=[EntityType.QUANTITY],
        confidence_threshold=0.90,
        priority=IntentPriority.HIGH
    ),
}