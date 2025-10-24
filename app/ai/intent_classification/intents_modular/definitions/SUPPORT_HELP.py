from ..models import IntentDefinition
from ..enums import IntentCategory, ActionCode, IntentPriority, EntityType

support_help_intent_definitions = {
    # 7.0 Support, Help & FAQ
    "contact_support": IntentDefinition(
        category=IntentCategory.SUPPORT_HELP,
        action_code=ActionCode.CONTACT_SUPPORT,
        description="User wants to contact customer support",
        example_phrases=[
            "I need help",
            "Contact support",
            "I want to talk to someone",
            "Get help",
            "Support please",
            "I need assistance",
            "Contact customer service",
            "Help me"
        ],
        required_entities=[],
        optional_entities=[EntityType.ISSUE_TYPE, EntityType.URGENCY],
        confidence_threshold=0.90,
        priority=IntentPriority.HIGH
    ),



    "report_issue": IntentDefinition(
        category=IntentCategory.SUPPORT_HELP,
        action_code=ActionCode.REPORT_ISSUE,
        description="User wants to report an issue",
        example_phrases=[
            "I want to report an issue",
            "Report problem",
            "I have an issue",
            "Report bug",
            "Something is wrong",
            "I found a problem",
            "Report issue",
            "I need to report something"
        ],
        required_entities=[],
        optional_entities=[EntityType.ISSUE_TYPE, EntityType.URGENCY],
        confidence_threshold=0.90,
        priority=IntentPriority.HIGH
    ),


    "help_general": IntentDefinition(
        category=IntentCategory.SUPPORT_HELP,
        action_code=ActionCode.HELP_GENERAL,
        description="User wants general help or assistance",
        example_phrases=[
            "I need help",
            "Help me",
            "I'm confused",
            "How does this work?",
            "I don't understand",
            "Can you help?",
            "I need assistance",
            "Help please"
        ],
        required_entities=[],
        optional_entities=[EntityType.QUESTION, EntityType.TOPIC],
        confidence_threshold=0.80,
        priority=IntentPriority.MEDIUM
    ),


    "faq_shipping": IntentDefinition(
        category=IntentCategory.SUPPORT_HELP,
        action_code=ActionCode.FAQ_SHIPPING,
        description="User has questions about shipping",
        example_phrases=[
            "How long does shipping take?",
            "Shipping information",
            "When will it arrive?",
            "Shipping times",
            "Delivery information",
            "How fast is shipping?",
            "Shipping options",
            "Delivery times"
        ],
        required_entities=[],
        optional_entities=[EntityType.ORDER_ID],
        confidence_threshold=0.85,
        priority=IntentPriority.HIGH
    ),

    "faq_payment": IntentDefinition(
        category=IntentCategory.SUPPORT_HELP,
        action_code=ActionCode.FAQ_PAYMENT,
        description="User has questions about payment",
        example_phrases=[
            "How do I pay?",
            "Payment methods",
            "What payment options?",
            "How to pay",
            "Payment information",
            "Payment help",
            "Payment questions",
            "How can I pay?"
        ],
        required_entities=[],
        optional_entities=[],
        confidence_threshold=0.85,
        priority=IntentPriority.HIGH
    ),




    
}