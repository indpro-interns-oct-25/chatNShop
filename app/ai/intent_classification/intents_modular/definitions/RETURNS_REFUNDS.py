from ..models import IntentDefinition
from ..enums import IntentCategory, ActionCode, IntentPriority, EntityType

returns_refunds_intent_definitions = {
    # 9.0 Returns, Refunds & Warranty
    "view_return_policy": IntentDefinition(
        category=IntentCategory.RETURNS_REFUNDS,
        action_code=ActionCode.VIEW_RETURN_POLICY,
        description="User wants to see the return policy",
        example_phrases=[
            "What's the return policy?",
            "Show me return policy",
            "Return policy",
            "How do returns work?",
            "Return information",
            "Return terms",
            "Return conditions",
            "Return rules"
        ],
        required_entities=[],
        optional_entities=[],
        confidence_threshold=0.85,
        priority=IntentPriority.MEDIUM
    ),

    "initiate_return": IntentDefinition(
        category=IntentCategory.RETURNS_REFUNDS,
        action_code=ActionCode.INITIATE_RETURN,
        description="User wants to start a return process",
        example_phrases=[
            "I want to return this",
            "Start return process",
            "Initiate return",
            "Return this item",
            "I need to return",
            "Begin return",
            "Start return",
            "Return this product"
        ],
        required_entities=[EntityType.ORDER_ID],
        optional_entities=[EntityType.REASON, EntityType.RETURN_REASON],
        confidence_threshold=0.90,
        priority=IntentPriority.HIGH
    ),

    "return_status": IntentDefinition(
        category=IntentCategory.RETURNS_REFUNDS,
        action_code=ActionCode.RETURN_STATUS,
        description="User wants to check the status of their return",
        example_phrases=[
            "What's my return status?",
            "Return status",
            "How is my return?",
            "Return progress",
            "Return update",
            "Status of return",
            "Return information",
            "Check return status"
        ],
        required_entities=[EntityType.ORDER_ID],
        optional_entities=[],
        confidence_threshold=0.85,
        priority=IntentPriority.HIGH
    ),

    "refund_request": IntentDefinition(
        category=IntentCategory.RETURNS_REFUNDS,
        action_code=ActionCode.REFUND_REQUEST,
        description="User wants to request a refund",
        example_phrases=[
            "I want a refund",
            "Request refund",
            "Refund my money",
            "I need a refund",
            "Refund request",
            "Give me refund",
            "Process refund",
            "Refund this order"
        ],
        required_entities=[EntityType.ORDER_ID],
        optional_entities=[EntityType.REASON],
        confidence_threshold=0.90,
        priority=IntentPriority.HIGH
    ),

    "track_return": IntentDefinition(
        category=IntentCategory.RETURNS_REFUNDS,
        action_code=ActionCode.TRACK_RETURN,
        description="User wants to track their return",
        example_phrases=[
            "Track my return",
            "Where is my return?",
            "Return tracking",
            "Track return package",
            "Return status",
            "Where's my return?",
            "Track return shipment",
            "Return package tracking"
        ],
        required_entities=[EntityType.ORDER_ID],
        optional_entities=[],
        confidence_threshold=0.85,
        priority=IntentPriority.HIGH
    ),
}