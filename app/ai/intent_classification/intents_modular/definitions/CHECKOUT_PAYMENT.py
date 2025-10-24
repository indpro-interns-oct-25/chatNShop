from ..models import IntentDefinition
from ..enums import IntentCategory, ActionCode, IntentPriority, EntityType

checkout_payment_intent_definitions = {
    # 4.0 Checkout & Payment
    "checkout_initiate": IntentDefinition(
        category=IntentCategory.CHECKOUT_PAYMENT,
        action_code=ActionCode.CHECKOUT_INITIATE,
        description="User wants to start the checkout process",
        example_phrases=[
            "I want to checkout",
            "Proceed to checkout",
            "Start checkout",
            "Begin checkout",
            "Checkout now",
            "I'm ready to buy",
            "Complete purchase",
            "Go to checkout"
        ],
        required_entities=[],
        optional_entities=[],
        confidence_threshold=0.90,
        priority=IntentPriority.CRITICAL
    ),

    "add_new_address": IntentDefinition(
        category=IntentCategory.CHECKOUT_PAYMENT,
        action_code=ActionCode.ADD_NEW_ADDRESS,
        description="User wants to add a new shipping address",
        example_phrases=[
            "Add new address",
            "I want to add an address",
            "Create new address",
            "Add another address",
            "New shipping address",
            "Add different address",
            "Create address",
            "Add address"
        ],
        required_entities=[],
        optional_entities=[EntityType.ADDRESS],
        confidence_threshold=0.85,
        priority=IntentPriority.HIGH
    ),

    "update_address": IntentDefinition(
        category=IntentCategory.CHECKOUT_PAYMENT,
        action_code=ActionCode.UPDATE_ADDRESS,
        description="User wants to update an existing address",
        example_phrases=[
            "Update my address",
            "Change address",
            "Edit address",
            "Modify address",
            "Update shipping address",
            "Change delivery address",
            "Edit my address",
            "Update address info"
        ],
        required_entities=[EntityType.ADDRESS],
        optional_entities=[],
        confidence_threshold=0.85,
        priority=IntentPriority.HIGH
    ),

    "payment_options": IntentDefinition(
        category=IntentCategory.CHECKOUT_PAYMENT,
        action_code=ActionCode.PAYMENT_OPTIONS,
        description="User wants to see available payment methods",
        example_phrases=[
            "What payment methods do you accept?",
            "Show payment options",
            "How can I pay?",
            "Payment methods",
            "What are my payment options?",
            "Show me payment choices",
            "Available payments",
            "Payment options"
        ],
        required_entities=[],
        optional_entities=[],
        confidence_threshold=0.85,
        priority=IntentPriority.HIGH
    ),

    "change_payment_method": IntentDefinition(
        category=IntentCategory.CHECKOUT_PAYMENT,
        action_code=ActionCode.CHANGE_PAYMENT_METHOD,
        description="User wants to change their payment method",
        example_phrases=[
            "Change payment method",
            "I want to use a different card",
            "Switch payment method",
            "Use different payment",
            "Change how I pay",
            "Switch to credit card",
            "Change payment",
            "Use another payment method"
        ],
        required_entities=[],
        optional_entities=[EntityType.PAYMENT_METHOD],
        confidence_threshold=0.85,
        priority=IntentPriority.HIGH
    ),

    "checkout_confirm": IntentDefinition(
        category=IntentCategory.CHECKOUT_PAYMENT,
        action_code=ActionCode.CHECKOUT_CONFIRM,
        description="User wants to confirm and complete their order",
        example_phrases=[
            "Confirm order",
            "Place order",
            "Complete purchase",
            "Confirm and pay",
            "Finalize order",
            "Complete checkout",
            "Place my order",
            "Confirm purchase"
        ],
        required_entities=[],
        optional_entities=[],
        confidence_threshold=0.90,
        priority=IntentPriority.CRITICAL
    ),
}