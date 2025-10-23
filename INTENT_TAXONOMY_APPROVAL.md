# Intent Taxonomy - Stakeholder Approval Document

## Executive Summary

This document presents the comprehensive intent taxonomy for the ChatNShop AI shopping assistant. The taxonomy defines all possible user intents, standardized action codes, and provides extensive mapping documentation for stakeholder review and approval.

## Intent Categories Overview

The system supports **7 main intent categories** with **35+ specific intents** and **50+ action codes**:

### 1. Product Discovery & Search (6 intents)
- **SEARCH**: General product search queries
- **PRODUCT_INFO**: Detailed product information requests
- **BROWSE**: General browsing without specific criteria
- **FILTER**: Applying filters to product results
- **SORT**: Sorting product results
- **COMPARE**: Comparing multiple products

### 2. Shopping Cart Operations (5 intents)
- **ADD_TO_CART**: Adding products to shopping cart
- **REMOVE_FROM_CART**: Removing products from cart
- **UPDATE_CART**: Modifying cart contents
- **VIEW_CART**: Viewing cart contents
- **CLEAR_CART**: Clearing all cart items

### 3. Checkout & Purchase (5 intents)
- **CHECKOUT**: Initiating checkout process
- **APPLY_COUPON**: Applying discount codes
- **REMOVE_COUPON**: Removing applied coupons
- **SELECT_PAYMENT**: Choosing payment methods
- **SELECT_SHIPPING**: Selecting shipping options

### 4. User Account & Preferences (7 intents)
- **LOGIN**: User authentication
- **LOGOUT**: User logout
- **REGISTER**: User registration
- **VIEW_PROFILE**: Viewing user profile
- **UPDATE_PROFILE**: Updating user information
- **VIEW_ORDERS**: Viewing order history
- **TRACK_ORDER**: Tracking order status

### 5. Customer Support & Help (5 intents)
- **FAQ**: Frequently asked questions
- **CONTACT_SUPPORT**: Contacting customer support
- **COMPLAINT**: Submitting complaints
- **RETURN_ITEM**: Returning purchased items
- **REFUND**: Requesting refunds

### 6. Recommendations & Personalization (4 intents)
- **RECOMMENDATIONS**: Getting product recommendations
- **WISHLIST_ADD**: Adding to wishlist
- **WISHLIST_REMOVE**: Removing from wishlist
- **WISHLIST_VIEW**: Viewing wishlist

### 7. General Interaction (5 intents)
- **GREETING**: Greeting the assistant
- **GOODBYE**: Saying goodbye
- **THANKS**: Expressing gratitude
- **CLARIFICATION**: Requesting clarification
- **UNKNOWN**: Unrecognized intents

## Key Action Codes

### High-Priority Actions (Critical for Business)
- `SEARCH_PRODUCTS` - Core product discovery
- `ADD_ITEM_TO_CART` - Revenue generation
- `INITIATE_CHECKOUT` - Purchase completion
- `GET_PRODUCT_DETAILS` - Product information
- `VIEW_CART_CONTENTS` - Cart management

### Medium-Priority Actions (Important for UX)
- `APPLY_FILTERS` - Product filtering
- `COMPARE_PRODUCTS` - Product comparison
- `GET_PERSONALIZED_RECOMMENDATIONS` - Personalization
- `VIEW_ORDER_HISTORY` - Account management
- `GET_FAQ_ANSWER` - Customer support

### Low-Priority Actions (Nice to have)
- `SEND_GREETING` - General interaction
- `ADD_TO_WISHLIST` - User engagement
- `TRACK_ORDER_STATUS` - Order tracking
- `CONTACT_CUSTOMER_SUPPORT` - Support escalation

## Example Phrase Mappings

### Product Search Examples
| User Input | Action Code | Business Impact |
|------------|-------------|-----------------|
| "I'm looking for a laptop" | `SEARCH_PRODUCTS` | High - Direct product discovery |
| "Show me electronics" | `SEARCH_BY_CATEGORY` | High - Category browsing |
| "Filter by price under $100" | `APPLY_FILTERS` | Medium - Refined search |

### Cart Operations Examples
| User Input | Action Code | Business Impact |
|------------|-------------|-----------------|
| "Add this to my cart" | `ADD_ITEM_TO_CART` | Critical - Revenue generation |
| "Show my cart" | `VIEW_CART_CONTENTS` | High - Cart management |
| "Clear my cart" | `CLEAR_CART_CONTENTS` | Medium - Cart control |

### Checkout Examples
| User Input | Action Code | Business Impact |
|------------|-------------|-----------------|
| "I'm ready to checkout" | `INITIATE_CHECKOUT` | Critical - Purchase completion |
| "Apply coupon code SAVE20" | `APPLY_DISCOUNT_CODE` | High - Promotional engagement |
| "Pay with credit card" | `SELECT_PAYMENT_METHOD` | High - Payment processing |

## Entity Requirements

### Critical Entities (Required for Core Functionality)
- **product_query**: Search terms for products
- **product_id**: Unique product identifier
- **quantity**: Number of items
- **order_id**: Order identifier

### Important Entities (Enhance User Experience)
- **category**: Product category name
- **brand**: Product brand name
- **price_range**: Price range specification
- **coupon_code**: Discount code

### Optional Entities (Nice to have)
- **size**: Product size
- **color**: Product color
- **date_range**: Time period
- **urgency**: Support urgency level

## Technical Implementation

### Confidence Thresholds
- **Default**: 0.7 (70% confidence required)
- **Critical Actions**: 0.8 (80% confidence for checkout/payment)
- **Low Priority**: 0.6 (60% confidence for greetings)

### Priority Levels
- **Priority 1**: Critical actions (checkout, payment)
- **Priority 2**: High importance (search, cart operations)
- **Priority 3**: Medium importance (browsing, recommendations)
- **Priority 4**: Low importance (general interaction)
- **Priority 5**: Fallback (unknown intents)

## Business Benefits

### Revenue Impact
- **Direct**: Improved product discovery → increased sales
- **Indirect**: Better cart management → reduced abandonment
- **Long-term**: Personalized recommendations → customer retention

### User Experience Impact
- **Efficiency**: Faster product search and filtering
- **Accuracy**: Precise intent recognition
- **Satisfaction**: Reduced friction in shopping flow

### Operational Impact
- **Support**: Automated FAQ handling
- **Analytics**: Better understanding of user behavior
- **Scalability**: Consistent intent processing

## Risk Assessment

### Low Risk
- **General intents**: Greeting, goodbye, thanks
- **Information intents**: Product details, FAQ
- **Account intents**: Login, profile viewing

### Medium Risk
- **Cart operations**: Add/remove items
- **Search intents**: Product discovery
- **Recommendations**: Personalized suggestions

### High Risk
- **Checkout intents**: Payment processing
- **Order management**: Returns, refunds
- **Support escalation**: Customer complaints

## Recommendations for Approval

### Immediate Approval Recommended
1. **Core shopping intents**: Search, cart, checkout
2. **Product information intents**: Details, comparison
3. **Account management intents**: Login, orders

### Conditional Approval Recommended
1. **Advanced features**: Recommendations, wishlist
2. **Support intents**: FAQ, contact support
3. **Personalization intents**: Profile updates

### Further Review Required
1. **Complex multi-intent scenarios**
2. **Industry-specific terminology**
3. **Regional language variations**

## Implementation Timeline

### Phase 1 (Immediate - 2 weeks)
- Core shopping intents (search, cart, checkout)
- Basic product information intents
- Essential account management intents

### Phase 2 (Short-term - 4 weeks)
- Advanced search and filtering
- Recommendations and personalization
- Customer support intents

### Phase 3 (Medium-term - 8 weeks)
- Complex multi-intent handling
- Advanced entity extraction
- Performance optimization

## Success Metrics

### Accuracy Metrics
- **Intent Classification Accuracy**: Target >90%
- **Entity Extraction Accuracy**: Target >85%
- **Response Relevance**: Target >80%

### Business Metrics
- **Cart Conversion Rate**: Target +15%
- **Search Success Rate**: Target +20%
- **Customer Satisfaction**: Target +10%

### Technical Metrics
- **Response Time**: Target <2 seconds
- **System Uptime**: Target >99.5%
- **Error Rate**: Target <1%

## Stakeholder Sign-off

### Required Approvals
- [ ] **Product Manager**: Intent categories and priorities
- [ ] **Engineering Lead**: Technical implementation approach
- [ ] **UX Designer**: User experience considerations
- [ ] **Business Analyst**: Business impact assessment
- [ ] **QA Lead**: Testing and validation approach

### Approval Criteria
- [ ] Intent taxonomy covers all business requirements
- [ ] Action codes are standardized and consistent
- [ ] Entity requirements are clearly defined
- [ ] Implementation approach is feasible
- [ ] Success metrics are measurable

## Next Steps

1. **Stakeholder Review**: 1 week for feedback and approval
2. **Technical Validation**: 1 week for implementation feasibility
3. **Pilot Testing**: 2 weeks for limited user testing
4. **Full Implementation**: 4 weeks for complete rollout
5. **Monitoring & Optimization**: Ongoing performance tracking

---

**Document Version**: 1.0  
**Last Updated**: [Current Date]  
**Next Review**: [Date + 1 month]  
**Owner**: AI Development Team  
**Approval Required By**: [Stakeholder Name]
