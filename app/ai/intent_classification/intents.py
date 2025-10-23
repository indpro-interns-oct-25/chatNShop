# app/ai/intent_classification/intents.py

"""
Intent examples used by the embedding matcher.
Edit / extend these phrases to improve coverage for each intent.
"""

INTENTS = {
    "add_to_cart": [
        "add this item to my cart",
        "put this in my shopping bag",
        "i want to buy this",
        "add to cart",
        "please add it to my cart",
        "can you put this in my cart"
    ],
    "search_product": [
        "find me shoes",
        "show me t-shirts",
        "search for a mobile",
        "look for laptop",
        "i'm looking for a sofa",
        "search for red sneakers"
    ],
    "view_cart": [
        "show my cart",
        "open shopping bag",
        "what's in my cart",
        "cart details",
        "view my cart"
    ],
    # add more intents & example phrases as needed
}
