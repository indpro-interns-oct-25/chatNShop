# Intent Mapping Examples

## Overview

This document provides comprehensive examples of how user phrases map to specific action codes in the ChatNShop intent classification system.

## Product Discovery & Search Mappings

### SEARCH_PRODUCTS
| User Phrase | Action Code | Extracted Entities |
|-------------|-------------|-------------------|
| "I'm looking for a laptop" | `SEARCH_PRODUCTS` | product_query: "laptop" |
| "Show me smartphones" | `SEARCH_PRODUCTS` | product_query: "smartphones" |
| "Find me running shoes" | `SEARCH_PRODUCTS` | product_query: "running shoes" |
| "Search for wireless headphones" | `SEARCH_PRODUCTS` | product_query: "wireless headphones" |
| "I need a coffee maker" | `SEARCH_PRODUCTS` | product_query: "coffee maker" |
| "Can you find me a good camera?" | `SEARCH_PRODUCTS` | product_query: "good camera" |

### SEARCH_BY_CATEGORY
| User Phrase | Action Code | Extracted Entities |
|-------------|-------------|-------------------|
| "Show me electronics" | `SEARCH_BY_CATEGORY` | category: "electronics" |
| "I want to see clothing" | `SEARCH_BY_CATEGORY` | category: "clothing" |
| "Browse home and garden" | `SEARCH_BY_CATEGORY` | category: "home and garden" |
| "What's in the sports section?" | `SEARCH_BY_CATEGORY` | category: "sports" |
| "Show me beauty products" | `SEARCH_BY_CATEGORY` | category: "beauty" |

### GET_PRODUCT_DETAILS
| User Phrase | Action Code | Extracted Entities |
|-------------|-------------|-------------------|
| "Tell me about this iPhone" | `GET_PRODUCT_DETAILS` | product_id: "iPhone" |
| "What are the specs of this laptop?" | `GET_PRODUCT_DETAILS` | product_id: "laptop" |
| "Show me product details" | `GET_PRODUCT_DETAILS` | product_id: [context] |
| "What's the warranty on this?" | `GET_PRODUCT_DETAILS` | product_id: [context] |
| "Is this product in stock?" | `GET_PRODUCT_DETAILS` | product_id: [context] |

### BROWSE_CATEGORIES
| User Phrase | Action Code | Extracted Entities |
|-------------|-------------|-------------------|
| "What's new?" | `BROWSE_CATEGORIES` | - |
| "Show me what's popular" | `BROWSE_CATEGORIES` | - |
| "Browse deals" | `BROWSE_CATEGORIES` | - |
| "What's trending?" | `BROWSE_CATEGORIES` | - |
| "Show me featured products" | `BROWSE_CATEGORIES` | - |

### APPLY_FILTERS
| User Phrase | Action Code | Extracted Entities |
|-------------|-------------|-------------------|
| "Filter by price under $100" | `APPLY_FILTERS` | filter_criteria: "price", filter_value: "<100" |
| "Show only red items" | `APPLY_FILTERS` | filter_criteria: "color", filter_value: "red" |
| "Filter by brand Apple" | `APPLY_FILTERS` | filter_criteria: "brand", filter_value: "Apple" |
| "Show items with free shipping" | `APPLY_FILTERS` | filter_criteria: "shipping", filter_value: "free" |
| "Filter by rating 4+ stars" | `APPLY_FILTERS` | filter_criteria: "rating", filter_value: "4+" |

### SORT_PRODUCTS
| User Phrase | Action Code | Extracted Entities |
|-------------|-------------|-------------------|
| "Sort by price low to high" | `SORT_PRODUCTS` | sort_criteria: "price", sort_order: "asc" |
| "Show cheapest first" | `SORT_PRODUCTS` | sort_criteria: "price", sort_order: "asc" |
| "Sort by newest" | `SORT_PRODUCTS` | sort_criteria: "date", sort_order: "desc" |
| "Sort by rating" | `SORT_PRODUCTS` | sort_criteria: "rating", sort_order: "desc" |
| "Sort by popularity" | `SORT_PRODUCTS` | sort_criteria: "popularity", sort_order: "desc" |

### COMPARE_PRODUCTS
| User Phrase | Action Code | Extracted Entities |
|-------------|-------------|-------------------|
| "Compare these two laptops" | `COMPARE_PRODUCTS` | product_ids: [context] |
| "Show me differences between these phones" | `COMPARE_PRODUCTS` | product_ids: [context] |
| "Which is better between these options?" | `COMPARE_PRODUCTS` | product_ids: [context] |
| "Compare features" | `COMPARE_PRODUCTS` | product_ids: [context] |
| "Side by side comparison" | `COMPARE_PRODUCTS` | product_ids: [context] |

## Shopping Cart Operations Mappings

### ADD_ITEM_TO_CART
| User Phrase | Action Code | Extracted Entities |
|-------------|-------------|-------------------|
| "Add this to my cart" | `ADD_ITEM_TO_CART` | product_id: [context] |
| "I want to buy this" | `ADD_ITEM_TO_CART` | product_id: [context] |
| "Add to cart" | `ADD_ITEM_TO_CART` | product_id: [context] |
| "Put this in my basket" | `ADD_ITEM_TO_CART` | product_id: [context] |
| "I'll take this one" | `ADD_ITEM_TO_CART` | product_id: [context] |
| "Add 2 of these to cart" | `ADD_ITEM_TO_CART` | product_id: [context], quantity: "2" |

### REMOVE_ITEM_FROM_CART
| User Phrase | Action Code | Extracted Entities |
|-------------|-------------|-------------------|
| "Remove this from my cart" | `REMOVE_ITEM_FROM_CART` | product_id: [context] |
| "Take this out of my basket" | `REMOVE_ITEM_FROM_CART` | product_id: [context] |
| "I don't want this anymore" | `REMOVE_ITEM_FROM_CART` | product_id: [context] |
| "Delete this item" | `REMOVE_ITEM_FROM_CART` | product_id: [context] |
| "Remove from cart" | `REMOVE_ITEM_FROM_CART` | product_id: [context] |

### UPDATE_CART_QUANTITY
| User Phrase | Action Code | Extracted Entities |
|-------------|-------------|-------------------|
| "Change quantity to 2" | `UPDATE_CART_QUANTITY` | product_id: [context], quantity: "2" |
| "I want 3 of these" | `UPDATE_CART_QUANTITY` | product_id: [context], quantity: "3" |
| "Update quantity" | `UPDATE_CART_QUANTITY` | product_id: [context], quantity: [user input] |
| "Make it 5 instead" | `UPDATE_CART_QUANTITY` | product_id: [context], quantity: "5" |
| "Change to 1" | `UPDATE_CART_QUANTITY` | product_id: [context], quantity: "1" |

### VIEW_CART_CONTENTS
| User Phrase | Action Code | Extracted Entities |
|-------------|-------------|-------------------|
| "Show my cart" | `VIEW_CART_CONTENTS` | - |
| "What's in my basket?" | `VIEW_CART_CONTENTS` | - |
| "View cart" | `VIEW_CART_CONTENTS` | - |
| "Show cart contents" | `VIEW_CART_CONTENTS` | - |
| "What did I add?" | `VIEW_CART_CONTENTS` | - |

### CLEAR_CART_CONTENTS
| User Phrase | Action Code | Extracted Entities |
|-------------|-------------|-------------------|
| "Clear my cart" | `CLEAR_CART_CONTENTS` | - |
| "Empty my basket" | `CLEAR_CART_CONTENTS` | - |
| "Remove everything" | `CLEAR_CART_CONTENTS` | - |
| "Start over" | `CLEAR_CART_CONTENTS` | - |
| "Clear all items" | `CLEAR_CART_CONTENTS` | - |

## Checkout & Purchase Mappings

### INITIATE_CHECKOUT
| User Phrase | Action Code | Extracted Entities |
|-------------|-------------|-------------------|
| "I'm ready to checkout" | `INITIATE_CHECKOUT` | - |
| "Proceed to payment" | `INITIATE_CHECKOUT` | - |
| "Buy now" | `INITIATE_CHECKOUT` | - |
| "Complete purchase" | `INITIATE_CHECKOUT` | - |
| "Checkout" | `INITIATE_CHECKOUT` | - |

### APPLY_DISCOUNT_CODE
| User Phrase | Action Code | Extracted Entities |
|-------------|-------------|-------------------|
| "Apply coupon code SAVE20" | `APPLY_DISCOUNT_CODE` | coupon_code: "SAVE20" |
| "Use my discount code" | `APPLY_DISCOUNT_CODE` | coupon_code: [user input] |
| "Apply promo code" | `APPLY_DISCOUNT_CODE` | coupon_code: [user input] |
| "I have a coupon" | `APPLY_DISCOUNT_CODE` | coupon_code: [user input] |
| "Enter discount code" | `APPLY_DISCOUNT_CODE` | coupon_code: [user input] |

### SELECT_PAYMENT_METHOD
| User Phrase | Action Code | Extracted Entities |
|-------------|-------------|-------------------|
| "I want to pay with credit card" | `SELECT_PAYMENT_METHOD` | payment_method: "credit card" |
| "Use PayPal" | `SELECT_PAYMENT_METHOD` | payment_method: "PayPal" |
| "Pay with Apple Pay" | `SELECT_PAYMENT_METHOD` | payment_method: "Apple Pay" |
| "Change payment method" | `SELECT_PAYMENT_METHOD` | payment_method: [user selection] |
| "Select payment option" | `SELECT_PAYMENT_METHOD` | payment_method: [user selection] |

## User Account Mappings

### USER_LOGIN
| User Phrase | Action Code | Extracted Entities |
|-------------|-------------|-------------------|
| "I want to login" | `USER_LOGIN` | - |
| "Sign me in" | `USER_LOGIN` | - |
| "Log into my account" | `USER_LOGIN` | - |
| "Access my account" | `USER_LOGIN` | - |
| "Login" | `USER_LOGIN` | - |

### VIEW_ORDER_HISTORY
| User Phrase | Action Code | Extracted Entities |
|-------------|-------------|-------------------|
| "Show my orders" | `VIEW_ORDER_HISTORY` | - |
| "View order history" | `VIEW_ORDER_HISTORY` | - |
| "What did I buy before?" | `VIEW_ORDER_HISTORY` | - |
| "My past purchases" | `VIEW_ORDER_HISTORY` | - |
| "Order history" | `VIEW_ORDER_HISTORY` | - |

### TRACK_ORDER_STATUS
| User Phrase | Action Code | Extracted Entities |
|-------------|-------------|-------------------|
| "Where is my order?" | `TRACK_ORDER_STATUS` | order_id: [context] |
| "Track my package" | `TRACK_ORDER_STATUS` | order_id: [context] |
| "Order status" | `TRACK_ORDER_STATUS` | order_id: [context] |
| "When will it arrive?" | `TRACK_ORDER_STATUS` | order_id: [context] |
| "Shipping status" | `TRACK_ORDER_STATUS` | order_id: [context] |

## Customer Support Mappings

### GET_FAQ_ANSWER
| User Phrase | Action Code | Extracted Entities |
|-------------|-------------|-------------------|
| "How do I return an item?" | `GET_FAQ_ANSWER` | question: "return policy" |
| "What's your return policy?" | `GET_FAQ_ANSWER` | question: "return policy" |
| "How long does shipping take?" | `GET_FAQ_ANSWER` | question: "shipping time" |
| "Do you offer free shipping?" | `GET_FAQ_ANSWER` | question: "free shipping" |
| "What payment methods do you accept?" | `GET_FAQ_ANSWER` | question: "payment methods" |

### CONTACT_CUSTOMER_SUPPORT
| User Phrase | Action Code | Extracted Entities |
|-------------|-------------|-------------------|
| "I need help" | `CONTACT_CUSTOMER_SUPPORT` | - |
| "Contact support" | `CONTACT_CUSTOMER_SUPPORT` | - |
| "Speak to someone" | `CONTACT_CUSTOMER_SUPPORT` | - |
| "I have a problem" | `CONTACT_CUSTOMER_SUPPORT` | - |
| "Customer service" | `CONTACT_CUSTOMER_SUPPORT` | - |

### INITIATE_RETURN
| User Phrase | Action Code | Extracted Entities |
|-------------|-------------|-------------------|
| "I want to return this" | `INITIATE_RETURN` | order_id: [context] |
| "How do I return an item?" | `INITIATE_RETURN` | order_id: [context] |
| "Return policy" | `INITIATE_RETURN` | order_id: [context] |
| "I need to send this back" | `INITIATE_RETURN` | order_id: [context] |
| "Return request" | `INITIATE_RETURN` | order_id: [context] |

## Recommendations & Personalization Mappings

### GET_PERSONALIZED_RECOMMENDATIONS
| User Phrase | Action Code | Extracted Entities |
|-------------|-------------|-------------------|
| "What do you recommend?" | `GET_PERSONALIZED_RECOMMENDATIONS` | - |
| "Show me suggestions" | `GET_PERSONALIZED_RECOMMENDATIONS` | - |
| "What's popular?" | `GET_PERSONALIZED_RECOMMENDATIONS` | - |
| "Recommend something for me" | `GET_PERSONALIZED_RECOMMENDATIONS` | - |
| "What would I like?" | `GET_PERSONALIZED_RECOMMENDATIONS` | - |

### ADD_TO_WISHLIST
| User Phrase | Action Code | Extracted Entities |
|-------------|-------------|-------------------|
| "Add to wishlist" | `ADD_TO_WISHLIST` | product_id: [context] |
| "Save for later" | `ADD_TO_WISHLIST` | product_id: [context] |
| "I want to remember this" | `ADD_TO_WISHLIST` | product_id: [context] |
| "Add to favorites" | `ADD_TO_WISHLIST` | product_id: [context] |
| "Wishlist this" | `ADD_TO_WISHLIST` | product_id: [context] |

### VIEW_WISHLIST
| User Phrase | Action Code | Extracted Entities |
|-------------|-------------|-------------------|
| "Show my wishlist" | `VIEW_WISHLIST` | - |
| "View saved items" | `VIEW_WISHLIST` | - |
| "My favorites" | `VIEW_WISHLIST` | - |
| "Saved for later" | `VIEW_WISHLIST` | - |
| "Wishlist" | `VIEW_WISHLIST` | - |

## General Interaction Mappings

### SEND_GREETING
| User Phrase | Action Code | Extracted Entities |
|-------------|-------------|-------------------|
| "Hello" | `SEND_GREETING` | - |
| "Hi there" | `SEND_GREETING` | - |
| "Good morning" | `SEND_GREETING` | - |
| "Hey" | `SEND_GREETING` | - |
| "Greetings" | `SEND_GREETING` | - |

### SEND_GOODBYE
| User Phrase | Action Code | Extracted Entities |
|-------------|-------------|-------------------|
| "Goodbye" | `SEND_GOODBYE` | - |
| "See you later" | `SEND_GOODBYE` | - |
| "Bye" | `SEND_GOODBYE` | - |
| "Thanks, that's all" | `SEND_GOODBYE` | - |
| "Have a good day" | `SEND_GOODBYE` | - |

### SEND_THANKS
| User Phrase | Action Code | Extracted Entities |
|-------------|-------------|-------------------|
| "Thank you" | `SEND_THANKS` | - |
| "Thanks" | `SEND_THANKS` | - |
| "Much appreciated" | `SEND_THANKS` | - |
| "Great, thanks" | `SEND_THANKS` | - |
| "Perfect, thank you" | `SEND_THANKS` | - |

### HANDLE_UNKNOWN_INTENT
| User Phrase | Action Code | Extracted Entities |
|-------------|-------------|-------------------|
| "I don't understand" | `HANDLE_UNKNOWN_INTENT` | - |
| "What?" | `HANDLE_UNKNOWN_INTENT` | - |
| "Huh?" | `HANDLE_UNKNOWN_INTENT` | - |
| "Can you repeat that?" | `HANDLE_UNKNOWN_INTENT` | - |
| "I'm confused" | `HANDLE_UNKNOWN_INTENT` | - |

## Complex Intent Examples

### Multi-Entity Intents
| User Phrase | Action Code | Extracted Entities |
|-------------|-------------|-------------------|
| "Show me red Nike shoes under $100" | `SEARCH_PRODUCTS` | product_query: "Nike shoes", color: "red", price_range: "<100" |
| "Add 2 large blue shirts to cart" | `ADD_ITEM_TO_CART` | product_query: "shirts", quantity: "2", size: "large", color: "blue" |
| "Compare iPhone 14 vs Samsung Galaxy S23" | `COMPARE_PRODUCTS` | product_ids: ["iPhone 14", "Samsung Galaxy S23"] |
| "Filter laptops by price $500-$1000 and brand Dell" | `APPLY_FILTERS` | filter_criteria: ["price", "brand"], filter_value: ["500-1000", "Dell"] |

### Context-Dependent Intents
| User Phrase | Action Code | Extracted Entities |
|-------------|-------------|-------------------|
| "Add this to cart" (while viewing product) | `ADD_ITEM_TO_CART` | product_id: [current product] |
| "Tell me more about this" (while viewing product) | `GET_PRODUCT_DETAILS` | product_id: [current product] |
| "Remove this" (while viewing cart) | `REMOVE_ITEM_FROM_CART` | product_id: [selected item] |
| "Track this order" (while viewing order history) | `TRACK_ORDER_STATUS` | order_id: [selected order] |

## Ambiguous Intent Handling

### Low Confidence Scenarios
| User Phrase | Possible Intents | Clarification Needed |
|-------------|------------------|-------------------|
| "I want this" | ADD_TO_CART, ADD_TO_WISHLIST | "Would you like to add this to your cart or wishlist?" |
| "Show me more" | BROWSE_CATEGORIES, GET_RECOMMENDATIONS | "Would you like to browse more products or see recommendations?" |
| "Help me" | CONTACT_SUPPORT, GET_FAQ_ANSWER | "What kind of help do you need? Support or information?" |

### Multi-Intent Phrases
| User Phrase | Primary Intent | Secondary Intent |
|-------------|----------------|------------------|
| "I want to buy this laptop and add it to my wishlist" | ADD_TO_CART | ADD_TO_WISHLIST |
| "Show me this product and compare it with similar items" | GET_PRODUCT_DETAILS | COMPARE_PRODUCTS |
| "I need help with my order and want to return an item" | CONTACT_SUPPORT | INITIATE_RETURN |

## Entity Extraction Patterns

### Product Query Patterns
- **Direct mention**: "laptop", "smartphone", "running shoes"
- **With adjectives**: "good laptop", "cheap smartphone", "comfortable shoes"
- **With specifications**: "wireless headphones", "4K TV", "gaming laptop"
- **With brand**: "Apple iPhone", "Nike shoes", "Samsung Galaxy"

### Quantity Patterns
- **Numbers**: "2", "three", "five"
- **Relative terms**: "more", "less", "another", "one more"
- **Range terms**: "a few", "several", "some"

### Price Range Patterns
- **Exact amounts**: "$100", "50 dollars"
- **Ranges**: "$50-$100", "under $200", "over $500"
- **Relative terms**: "cheap", "expensive", "affordable", "budget"

### Time Patterns
- **Immediate**: "now", "today", "asap"
- **Future**: "tomorrow", "next week", "soon"
- **Past**: "yesterday", "last week", "recently"

This comprehensive mapping provides the foundation for accurate intent classification and entity extraction in the ChatNShop system.
