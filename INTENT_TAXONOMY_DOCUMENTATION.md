# Intent Taxonomy Documentation

## Overview

This document provides comprehensive documentation for the ChatNShop intent classification system. It defines all possible user intents, their corresponding action codes, and example phrase mappings.

## Intent Categories

The system supports the following main intent categories:

### 1. Product Discovery & Search
- **SEARCH**: General product search queries
- **PRODUCT_INFO**: Requests for detailed product information
- **BROWSE**: General browsing without specific criteria
- **FILTER**: Applying filters to product results
- **SORT**: Sorting product results
- **COMPARE**: Comparing multiple products

### 2. Shopping Cart Operations
- **ADD_TO_CART**: Adding products to shopping cart
- **REMOVE_FROM_CART**: Removing products from cart
- **UPDATE_CART**: Modifying cart contents
- **VIEW_CART**: Viewing cart contents
- **CLEAR_CART**: Clearing all cart items

### 3. Checkout & Purchase
- **CHECKOUT**: Initiating checkout process
- **APPLY_COUPON**: Applying discount codes
- **REMOVE_COUPON**: Removing applied coupons
- **SELECT_PAYMENT**: Choosing payment methods
- **SELECT_SHIPPING**: Selecting shipping options

### 4. User Account & Preferences
- **LOGIN**: User authentication
- **LOGOUT**: User logout
- **REGISTER**: User registration
- **VIEW_PROFILE**: Viewing user profile
- **UPDATE_PROFILE**: Updating user information
- **VIEW_ORDERS**: Viewing order history
- **TRACK_ORDER**: Tracking order status

### 5. Customer Support & Help
- **FAQ**: Frequently asked questions
- **CONTACT_SUPPORT**: Contacting customer support
- **COMPLAINT**: Submitting complaints
- **RETURN_ITEM**: Returning purchased items
- **REFUND**: Requesting refunds

### 6. Recommendations & Personalization
- **RECOMMENDATIONS**: Getting product recommendations
- **WISHLIST_ADD**: Adding to wishlist
- **WISHLIST_REMOVE**: Removing from wishlist
- **WISHLIST_VIEW**: Viewing wishlist

### 7. General Interaction
- **GREETING**: Greeting the assistant
- **GOODBYE**: Saying goodbye
- **THANKS**: Expressing gratitude
- **CLARIFICATION**: Requesting clarification
- **UNKNOWN**: Unrecognized intents

## Action Codes

Each intent maps to a specific action code that the system can execute:

### Product Discovery & Search Actions
- `SEARCH_PRODUCTS`: Search for products by query
- `SEARCH_BY_CATEGORY`: Search within specific category
- `SEARCH_BY_BRAND`: Search by brand name
- `SEARCH_BY_PRICE_RANGE`: Search within price range
- `GET_PRODUCT_DETAILS`: Retrieve product information
- `GET_PRODUCT_REVIEWS`: Get product reviews
- `GET_PRODUCT_AVAILABILITY`: Check product availability
- `BROWSE_CATEGORIES`: Browse product categories
- `BROWSE_DEALS`: Browse special deals
- `BROWSE_NEW_ARRIVALS`: Browse new products
- `APPLY_FILTERS`: Apply product filters
- `CLEAR_FILTERS`: Clear applied filters
- `SORT_PRODUCTS`: Sort product results
- `COMPARE_PRODUCTS`: Compare multiple products

### Shopping Cart Actions
- `ADD_ITEM_TO_CART`: Add product to cart
- `REMOVE_ITEM_FROM_CART`: Remove product from cart
- `UPDATE_CART_QUANTITY`: Update item quantity
- `VIEW_CART_CONTENTS`: Display cart contents
- `CLEAR_CART_CONTENTS`: Clear all cart items
- `GET_CART_SUBTOTAL`: Calculate cart subtotal
- `GET_CART_TOTAL`: Calculate cart total

### Checkout & Purchase Actions
- `INITIATE_CHECKOUT`: Start checkout process
- `APPLY_DISCOUNT_CODE`: Apply coupon/discount
- `REMOVE_DISCOUNT_CODE`: Remove applied discount
- `SELECT_PAYMENT_METHOD`: Choose payment method
- `SELECT_SHIPPING_METHOD`: Choose shipping option
- `CONFIRM_ORDER`: Confirm purchase
- `CANCEL_ORDER`: Cancel order

### User Account Actions
- `USER_LOGIN`: Authenticate user
- `USER_LOGOUT`: Logout user
- `USER_REGISTER`: Register new user
- `VIEW_USER_PROFILE`: Display user profile
- `UPDATE_USER_PROFILE`: Update profile information
- `VIEW_ORDER_HISTORY`: Show order history
- `TRACK_ORDER_STATUS`: Track order progress
- `GET_ORDER_DETAILS`: Get order information

### Customer Support Actions
- `GET_FAQ_ANSWER`: Answer FAQ questions
- `CONTACT_CUSTOMER_SUPPORT`: Connect to support
- `SUBMIT_COMPLAINT`: Submit complaint
- `INITIATE_RETURN`: Start return process
- `REQUEST_REFUND`: Request refund
- `GET_SUPPORT_HOURS`: Get support availability

### Recommendations & Personalization Actions
- `GET_PERSONALIZED_RECOMMENDATIONS`: Get recommendations
- `ADD_TO_WISHLIST`: Add to wishlist
- `REMOVE_FROM_WISHLIST`: Remove from wishlist
- `VIEW_WISHLIST`: Display wishlist
- `GET_SIMILAR_PRODUCTS`: Find similar products
- `GET_FREQUENTLY_BOUGHT_TOGETHER`: Get bundle suggestions

### General Interaction Actions
- `SEND_GREETING`: Send greeting response
- `SEND_GOODBYE`: Send goodbye response
- `SEND_THANKS`: Send thanks response
- `REQUEST_CLARIFICATION`: Ask for clarification
- `HANDLE_UNKNOWN_INTENT`: Handle unrecognized intent

## Example Phrase Mappings

### Product Search Examples
| Phrase | Action Code |
|--------|-------------|
| "I'm looking for a laptop" | `SEARCH_PRODUCTS` |
| "Show me smartphones" | `SEARCH_PRODUCTS` |
| "Find me running shoes" | `SEARCH_PRODUCTS` |
| "Search for wireless headphones" | `SEARCH_PRODUCTS` |
| "Show me electronics" | `SEARCH_BY_CATEGORY` |
| "Browse home and garden" | `SEARCH_BY_CATEGORY` |

### Cart Operations Examples
| Phrase | Action Code |
|--------|-------------|
| "Add this to my cart" | `ADD_ITEM_TO_CART` |
| "I want to buy this" | `ADD_ITEM_TO_CART` |
| "Remove this from my cart" | `REMOVE_ITEM_FROM_CART` |
| "Show my cart" | `VIEW_CART_CONTENTS` |
| "What's in my basket?" | `VIEW_CART_CONTENTS` |
| "Clear my cart" | `CLEAR_CART_CONTENTS` |

### Checkout Examples
| Phrase | Action Code |
|--------|-------------|
| "I'm ready to checkout" | `INITIATE_CHECKOUT` |
| "Proceed to payment" | `INITIATE_CHECKOUT` |
| "Apply coupon code SAVE20" | `APPLY_DISCOUNT_CODE` |
| "I want to pay with credit card" | `SELECT_PAYMENT_METHOD` |
| "Use PayPal" | `SELECT_PAYMENT_METHOD` |

### User Account Examples
| Phrase | Action Code |
|--------|-------------|
| "I want to login" | `USER_LOGIN` |
| "Sign me in" | `USER_LOGIN` |
| "Show my orders" | `VIEW_ORDER_HISTORY` |
| "Where is my order?" | `TRACK_ORDER_STATUS` |
| "Track my package" | `TRACK_ORDER_STATUS` |

### Support Examples
| Phrase | Action Code |
|--------|-------------|
| "How do I return an item?" | `GET_FAQ_ANSWER` |
| "What's your return policy?" | `GET_FAQ_ANSWER` |
| "I need help" | `CONTACT_CUSTOMER_SUPPORT` |
| "I want to return this" | `INITIATE_RETURN` |

### Recommendations Examples
| Phrase | Action Code |
|--------|-------------|
| "What do you recommend?" | `GET_PERSONALIZED_RECOMMENDATIONS` |
| "Show me suggestions" | `GET_PERSONALIZED_RECOMMENDATIONS` |
| "Add to wishlist" | `ADD_TO_WISHLIST` |
| "Save for later" | `ADD_TO_WISHLIST` |
| "Show my wishlist" | `VIEW_WISHLIST` |

### General Interaction Examples
| Phrase | Action Code |
|--------|-------------|
| "Hello" | `SEND_GREETING` |
| "Hi there" | `SEND_GREETING` |
| "Goodbye" | `SEND_GOODBYE` |
| "Thank you" | `SEND_THANKS` |
| "I don't understand" | `HANDLE_UNKNOWN_INTENT` |

## Entity Requirements

Each intent may require specific entities to be extracted from user input:

### Required Entities
- **product_query**: Search terms for products
- **product_id**: Unique product identifier
- **category**: Product category name
- **order_id**: Order identifier
- **coupon_code**: Discount code
- **payment_method**: Payment option
- **quantity**: Number of items
- **filter_criteria**: Filter type
- **sort_criteria**: Sort type

### Optional Entities
- **brand**: Product brand name
- **price_range**: Price range specification
- **size**: Product size
- **color**: Product color
- **subcategory**: Product subcategory
- **date_range**: Time period
- **reason**: Return/complaint reason
- **urgency**: Support urgency level

## Confidence Thresholds

Each intent has a confidence threshold (default: 0.7) that determines when the system should be confident enough to execute the action. Lower confidence scores may trigger clarification requests.

## Priority Levels

Intents are assigned priority levels (1-5) to handle conflicts and determine processing order:
- **Priority 1**: Critical actions (checkout, payment)
- **Priority 2**: High importance (search, cart operations)
- **Priority 3**: Medium importance (browsing, recommendations)
- **Priority 4**: Low importance (general interaction)
- **Priority 5**: Fallback (unknown intents)

## Usage Examples

### Python API Usage

```python
from app.ai.intent_classification.intents import get_intent_taxonomy, get_action_code_for_phrase

# Get taxonomy instance
taxonomy = get_intent_taxonomy()

# Get action code for a phrase
action_code = get_action_code_for_phrase("I'm looking for a laptop")
# Returns: "SEARCH_PRODUCTS"

# Get intent definition
intent_def = taxonomy.get_intent_definition("search_products")
print(intent_def.description)
# Returns: "User wants to search for products"

# Get all categories
categories = taxonomy.get_all_categories()
print([cat.value for cat in categories])
# Returns: ['SEARCH', 'PRODUCT_INFO', 'BROWSE', ...]

# Get intents by category
search_intents = taxonomy.get_intents_by_category(IntentCategory.SEARCH)
```

### Intent Classification Flow

1. **Input Processing**: User phrase is received
2. **Intent Detection**: System analyzes phrase against intent definitions
3. **Entity Extraction**: Required entities are extracted from the phrase
4. **Confidence Scoring**: System calculates confidence score
5. **Action Execution**: If confidence > threshold, execute corresponding action
6. **Response Generation**: Generate appropriate response to user

## Integration Notes

- The intent taxonomy is designed to be extensible
- New intents can be added by extending the `intents` dictionary
- Action codes should be unique and descriptive
- Example phrases should cover common variations
- Entity requirements should be clearly defined
- Confidence thresholds can be adjusted based on testing

## Testing & Validation

- Each intent should be tested with multiple example phrases
- Edge cases and ambiguous phrases should be handled
- Confidence scoring should be validated against human judgment
- Entity extraction accuracy should be measured
- Response quality should be evaluated

## Future Enhancements

- Multi-language support
- Context-aware intent classification
- Dynamic intent learning
- Advanced entity recognition
- Intent confidence calibration
- A/B testing framework for intent accuracy
