"""
Defines all supported user intents and example utterances
for both keyword-based and embedding-based classifiers.
"""

INTENT_EXAMPLES = {
    "ADD_TO_CART": [
        "add this to my cart",
        "put in my shopping cart",
        "buy this item",
        "I want to purchase this",
    ],
    "REMOVE_FROM_CART": [
        "remove from cart",
        "delete this item from cart",
        "cancel this product",
        "take this out of my cart",
    ],
    "CHECK_ORDER_STATUS": [
        "track my order",
        "check my delivery status",
        "where is my order",
        "order status please",
    ],
    "CREATE_ACCOUNT": [
        "sign up",
        "register new account",
        "create a profile",
        "make a new account",
    ],
    "REORDER": [
        "buy again",
        "reorder my last purchase",
        "order this item again",
    ],
    "SEARCH_PRODUCT": [
        "show me red shoes",
        "find blue t-shirts under 500",
        "search for iphone",
        "look for samsung phones",
        "show me blue jeans under 2000",
    ],
    "ORDER_FOOD": [
        "order pizza",
        "I want to order food",
        "buy a burger",
        "get me some fries",
        "order something to eat",
        "I want to eat something",
    ],
}
