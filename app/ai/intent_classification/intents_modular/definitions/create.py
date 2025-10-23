#-------------------- create intent definition files -------------------------------

# import os

# # Categories
# categories = [
#     "SEARCH_DISCOVERY","PRODUCT_DETAILS","CART_WISHLIST","CHECKOUT_PAYMENT",
#     "ORDERS_FULFILLMENT","ACCOUNT_PROFILE","NOTIFICATIONS_SUBSCRIPTIONS",
#     "SUPPORT_HELP","PROMOTIONS_LOYALTY","SELLER_MARKETPLACE","RETURNS_REFUNDS",
#     "REVIEWS_RATINGS","ANALYTICS_TRACKING","PERSONALIZATION","SEARCH_ADVANCED",
#     "VOICE_BOT","NAVIGATION","FILES_DOWNLOADS","LEGAL_PRIVACY","ADMIN_MODERATION",
#     "INTEGRATIONS","OFFLINE_STORES","FINANCE_INVOICING","MESSAGING","EXPERIMENTS",
#     "B2B_ENTERPRISE","LOYALTY_MEMBERSHIP","SEARCH_INSIGHTS","SEO_LINKS",
#     "HELPERS_FALLBACK","FINE_SEARCH","CART_EDGE_CASES","ORDER_SUBSCRIPTIONS",
#     "SECURITY_FRAUD","DATA_BACKUPS","SHOPPING_ASSISTANT","TAX_INTERNATIONAL",
#     "PAYMENTS_ADVANCED","OFFLINE_NOTIFICATIONS","PRODUCT_LIFECYCLE","COUPONS_VOUCHERS",
#     "FEEDBACK_SURVEYS","DEVICE_APP","CONTENT_GUIDES","SOCIAL_FEATURES",
#     "BILLING_ACCOUNTING","QA_DEVOPS","INVENTORY","GUIDANCE","MISCELLANEOUS","UNKNOWN"
# ]

# # Template for each definition file
# template = """from ..models import IntentDefinition
# from ..enums import IntentCategory, ActionCode, IntentPriority, EntityType

# {category_lower}_intent_definitions = {{
#     # TODO: Add intent definitions for {category}
# }}
# """

# # Generate files in current directory
# for cat in categories:
#     file_path = os.path.join(os.getcwd(), f"{cat}.py")
#     with open(file_path, "w") as f:
#         f.write(template.format(category_lower=cat.lower(), category=cat))

# # Create __init__.py in current directory
# init_file = os.path.join(os.getcwd(), "__init__.py")
# with open(init_file, "w") as f:
#     f.write("# Init file for definitions package\n")

# print(f"Created {len(categories)} definition files and __init__.py in the current folder")

#-------------------- end of create intent definition files -------------------------------

#--------------------- populate intent definitions -----------------------------

import os
from ..models import IntentDefinition
from ..enums import IntentCategory, ActionCode, IntentPriority, EntityType

unified_category_action_map = {
    # 1.0 - 1.4: Search, Discovery, Filters, Sorting
    "SEARCH_DISCOVERY": [
        "SEARCH_PRODUCT", "SEARCH_CATEGORY", "SEARCH_BRAND", "SEARCH_PRICE_RANGE", "SEARCH_COLOR",
        "SEARCH_SIZE", "SEARCH_RATING", "SEARCH_DISCOUNT", "SEARCH_BY_IMAGE", "SEARCH_BY_VOICE",
        "SEARCH_TRENDING", "SEARCH_RECENT", "SEARCH_NEARBY", "SEARCH_SIMILAR", "SEARCH_SAVED",
        "SEARCH_FEATURED", "SEARCH_NEW_ARRIVALS", "SEARCH_BESTSELLERS", "SEARCH_ON_SALE",
        "SEARCH_EXACT_MATCH", "PRODUCT_RECOMMENDATION", "PERSONALIZED_RECOMMENDATIONS",
        "RECOMMEND_FOR_OCCASION", "RECOMMEND_SIMILAR", "RECOMMEND_COMPLEMENTS", "VIEW_RECOMMENDED",
        "BROWSE_CURATED_LIST", "VIEW_FEATURED", "FILTER_PRICE", "FILTER_RATING", "FILTER_BRAND",
        "FILTER_AVAILABILITY", "FILTER_COLOR", "FILTER_SIZE", "FILTER_DISCOUNT", "APPLY_FILTERS",
        "REMOVE_FILTERS", "CLEAR_FILTER", "SORT_PRICE", "SORT_POPULARITY", "SORT_NEWEST",
        "SORT_RATING", "VIEW_GRID", "VIEW_LIST"
    ],
    # 2.0: Product Details
    "PRODUCT_DETAILS": [
        "PRODUCT_INFO", "PRODUCT_DETAILS", "PRODUCT_AVAILABILITY", "PRODUCT_PRICE",
        "PRODUCT_IMAGES", "PRODUCT_VIDEO", "PRODUCT_MANUAL", "PRODUCT_CERTIFICATION",
        "PRODUCT_WARRANTY", "PRODUCT_DIMENSIONS", "PRODUCT_WEIGHT", "PRODUCT_COLOR_OPTIONS",
        "PRODUCT_SIZE_OPTIONS", "PRODUCT_VARIANTS", "PRODUCT_SKU_INFO", "PRODUCT_TAGS",
        "PRODUCT_FAQ", "PRODUCT_REVIEWS", "PRODUCT_AVERAGE_REVIEW", "PRODUCT_RATING",
        "PRODUCT_COMPARISON", "COMPARE_FEATURE", "PRODUCT_ALTERNATIVES", "RELATED_ACCESSORIES",
        "PRODUCT_AVERAGE_PRICE", "VIEW_PRICE_HISTORY", "PRICE_ALERT", "NOTIFY_PRICE_DROP",
        "NOTIFY_RESTOCK", "CHECK_STOCK_NEARBY", "CHECK_STOCK_STORE", "PRODUCT_SHARE",
        "PRODUCT_CUSTOMIZATION", "REQUEST_QUOTE"
    ],
    # 3.0: Cart and Wishlist
    "CART_WISHLIST": [
        "ADD_TO_CART", "REMOVE_FROM_CART", "UPDATE_CART_QUANTITY", "VIEW_CART", "EMPTY_CART",
        "MOVE_TO_CART", "SAVE_FOR_LATER", "CART_TOTAL", "CART_ITEM_DETAILS", "APPLY_COUPON",
        "REMOVE_COUPON", "VIEW_WISHLIST", "ADD_TO_WISHLIST", "REMOVE_FROM_WISHLIST",
        "VIEW_RECENTLY_VIEWED", "CLEAR_RECENTLY_VIEWED", "FAVORITE_BRANDS", "MOVE_TO_WISHLIST",
        "GIFT_WRAP", "ADD_NOTE", "CART_SAVING"
    ],
    # 4.0: Checkout and Payment
    "CHECKOUT_PAYMENT": [
        "CHECKOUT_INITIATE", "CHECKOUT_ADDRESS", "ADD_NEW_ADDRESS", "UPDATE_ADDRESS",
        "DELETE_ADDRESS", "CHANGE_ADDRESS", "CHECKOUT_PAYMENT", "PAYMENT_OPTIONS",
        "CHANGE_PAYMENT_METHOD", "UPDATE_PAYMENT_METHOD", "CHECKOUT_CONFIRM",
        "PAYMENT_FAILED_HELP", "PAYMENT_SUCCESS", "PAYMENT_PENDING", "REFUND_STATUS",
        "PAYMENT_REFUND", "PAYMENT_RECEIPT", "GIFT_CARD_PURCHASE", "GIFT_CARD_BALANCE",
        "GIFT_CARD_REDEEM", "APPLY_GIFT_CARD"
    ],
    # 5.0: Orders and Fulfillment
    "ORDERS_FULFILLMENT": [
        "ORDER_STATUS", "ORDER_HISTORY", "ORDER_CANCEL", "ORDER_RETURN", "TRACK_SHIPMENT",
        "TRACK_RETURN", "CANCEL_RETURN", "REFUND_REQUEST", "REFUND_COMPLETE", "ORDER_INVOICE",
        "REORDER", "DELIVERY_STATUS", "DELIVERY_ESTIMATE", "SCHEDULE_DELIVERY",
        "CHANGE_DELIVERY_DATE", "SHIPMENT_DETAILS", "SHIPPING_COST", "SHIPPING_OPTIONS",
        "SHIP_TO_STORE", "PICKUP_STORE", "ORDER_MODIFY"
    ],
    # 6.0: Account, Auth & Profile
    "ACCOUNT_PROFILE": [
        "CREATE_ACCOUNT", "LOGIN", "LOGOUT", "LOGIN_STATUS", "LOGIN_WITH_SOCIAL",
        "FORGOT_PASSWORD", "RESET_PASSWORD", "CHANGE_PASSWORD", "UPDATE_PROFILE",
        "VIEW_PROFILE", "DELETE_ACCOUNT", "ACCOUNT_SECURITY", "TWO_FACTOR_SETUP",
        "TWO_FACTOR_VERIFY", "VERIFY_EMAIL", "RESEND_VERIFICATION", "LINK_ACCOUNTS",
        "UNLINK_ACCOUNT", "PROFILE_PICTURE_UPDATE", "PREFERENCES_UPDATE"
    ],
    # 7.0: Notifications & Subscriptions (Only notifications)
    "NOTIFICATIONS_SUBSCRIPTIONS": [
        "USER_NOTIFICATIONS", "ENABLE_NOTIFICATIONS", "DISABLE_NOTIFICATIONS",
        "SUBSCRIBE_NEWSLETTER", "UNSUBSCRIBE_NEWSLETTER", "NOTIFY_SALES",
        "NOTIFY_ORDERS", "NOTIFY_SHIPMENT", "NOTIFY_DELIVERY", "EMAIL_PREFERENCES",
        "SMS_PREFERENCES", "PUSH_PREFERENCES"
    ],
    # 8.0: Support, Help & FAQ
    "SUPPORT_HELP": [
        "CONTACT_SUPPORT", "LIVE_CHAT", "CALL_SUPPORT", "REQUEST_CALLBACK",
        "FEEDBACK_SUBMIT", "REPORT_ISSUE", "REPORT_PRODUCT", "HELP_GENERAL",
        "FAQ_RETURNS", "FAQ_SHIPPING", "FAQ_PAYMENT", "FAQ_ACCOUNT", "FAQ_COUPON",
        "FAQ_TECH_SUPPORT", "FAQ_DELIVERY", "FAQ_REFUND", "PAYMENT_HELP",
        "SECURITY_HELP"
    ],
    # 9.0: Promotions, Offers & Loyalty
    "PROMOTIONS_LOYALTY": [
        "VIEW_PROMOTIONS", "VIEW_COUPONS", "APPLY_PROMO", "REMOVE_PROMO",
        "VIEW_BESTSELLERS", "VIEW_NEW_ARRIVALS", "VIEW_SALE_COLLECTION",
        "LOYALTY_POINTS", "REDEEM_POINTS", "CHECK_REWARDS", "CLAIM_REWARD",
        "VIEW_GIFT_OPTIONS", "PRICE_DROP_ALERTS", "FLASH_SALE_INFO"
    ],
    # 10.0: Seller, Marketplace & Catalog
    "SELLER_MARKETPLACE": [
        "VIEW_SELLER_INFO", "CONTACT_SELLER", "VIEW_SELLER_RATINGS", "SELLER_POLICIES",
        "BULK_ORDER", "WHOLESALE_INQUIRY", "CORPORATE_ORDER", "LIST_PRODUCT",
        "UNLIST_PRODUCT", "UPDATE_PRODUCT_LISTING", "VERIFY_SELLER"
    ],
    # 11.0: Returns, Refunds & Warranty
    "RETURNS_REFUNDS": [
        "VIEW_RETURN_POLICY", "VIEW_WARRANTY_POLICY", "PRODUCT_RETURN_ELIGIBILITY",
        "INITIATE_RETURN", "RETURN_PICKUP_SCHEDULE", "RETURN_STATUS",
        "WARRANTY_CLAIM", "WARRANTY_STATUS"
    ],
    # 12.0: Reviews & Ratings
    "REVIEWS_RATINGS": [
        "ADD_REVIEW", "EDIT_REVIEW", "DELETE_REVIEW", "FLAG_REVIEW", "VIEW_REVIEWS",
        "REVIEW_RECOMMENDATION", "PRODUCT_AVERAGE_REVIEW"
    ],
    # 13.0: Analytics, Tracking & Metrics
    "ANALYTICS_TRACKING": [
        "TRACK_USER_ACTION", "TRACK_SEARCH_QUERY", "TRACK_CART_ABANDONMENT",
        "VIEW_ANALYTICS", "EXPORT_ANALYTICS", "LISTEN_BEHAVIOR"
    ],
    # 14.0: Account Preferences & Personalization
    "PERSONALIZATION": [
        "SET_LANGUAGE", "SET_CURRENCY", "SET_ADDRESS_PREFERENCE",
        "SET_PAYMENT_PREFERENCE", "MANAGE_ADDRESSES", "PREFERENCES_EXPORT",
        "PREFERENCES_IMPORT", "PERSONAL_PROFILE_SUMMARY"
    ],
    # 15.0: Search Advanced
    "SEARCH_ADVANCED": [
        "SEARCH_ADVANCED", "SEARCH_FUZZY", "SEARCH_PHRASE", "SEARCH_EXCLUDE",
        "SEARCH_BOOLEAN", "SEARCH_CUSTOM_FILTER", "SEARCH_BY_SKU"
    ],
    # 16.0: Voice, Assistants & Bot
    "VOICE_BOT": [
        "START_VOICE_SESSION", "END_VOICE_SESSION", "VOICE_HELP", "BOT_HANDOFF",
        "BOT_INTENT_CLARIFY", "BOT_FALLBACK"
    ],
    # 17.0: UI & Navigation
    "NAVIGATION": [
        "NAV_HOME", "NAV_CATEGORY", "NAV_CART", "NAV_WISHLIST", "NAV_ORDERS",
        "NAV_PROFILE", "NAV_SEARCH", "NAV_OFFERS", "NAV_HELP"
    ],
    # 18.0: Files, Downloads & Assets
    "FILES_DOWNLOADS": [
        "DOWNLOAD_INVOICE", "DOWNLOAD_MANUAL", "DOWNLOAD_RECEIPT", "APP_DOWNLOAD",
        "SHARE_PRODUCT_LINK"
    ],
    # 19.0: Privacy, Terms & Legal
    "LEGAL_PRIVACY": [
        "PRIVACY_POLICY", "TERMS_AND_CONDITIONS", "DATA_REQUEST",
        "DATA_DELETE_REQUEST", "COOKIE_PREFERENCES"
    ],
    # 20.0: Admin, Moderation & Safety
    "ADMIN_MODERATION": [
        "FLAG_CONTENT", "REVIEW_FLAGGED_CONTENT", "BAN_USER", "UNBAN_USER",
        "GRANT_ADMIN", "REVOKE_ADMIN", "VIEW_AUDIT_LOGS", "EXPORT_AUDIT_LOGS",
        "MODERATION_ACTION"
    ],
    # 21.0: Integrations & Third-Party
    "INTEGRATIONS": [
        "CONNECT_PAYMENT_GATEWAY", "DISCONNECT_PAYMENT_GATEWAY",
        "CONNECT_SHIPPING_PROVIDER", "DISCONNECT_SHIPPING_PROVIDER",
        "SYNC_INVENTORY", "SYNC_ORDERS"
    ],
    # 22.0: Offline, Stores & Pickup
    "OFFLINE_STORES": [
        "STORE_LOCATOR", "CHECK_STORE_STOCK", "RESERVE_IN_STORE",
        "SCHEDULE_PICKUP", "CANCEL_PICKUP"
    ],
    # 23.0: Marketplace Finance & Invoicing
    "FINANCE_INVOICING": [
        "REQUEST_INVOICE", "SUBMIT_TAX_INFO", "VIEW_PAYOUTS", "REQUEST_PAYOUT"
    ],
    # 24.0: Messaging & Communication
    "MESSAGING": [
        "SEND_MESSAGE_TO_SELLER", "VIEW_MESSAGES", "DELETE_MESSAGE",
        "MARK_MESSAGE_READ", "MARK_MESSAGE_UNREAD"
    ],
    # 25.0: Experiments, Features & Flags
    "EXPERIMENTS": [
        "ENABLE_EXPERIMENT", "DISABLE_EXPERIMENT", "GET_EXPERIMENT_STATUS"
    ],
    # 26.0: B2B & Enterprise
    "B2B_ENTERPRISE": [
        "REQUEST_CORPORATE_ACCOUNT", "VIEW_ENTERPRISE_PRICING",
        "REQUEST_DEMO", "ENTERPRISE_BULK_ORDER"
    ],
    # 27.0: Loyalty & Membership
    "LOYALTY_MEMBERSHIP": [
        "VIEW_MEMBERSHIP", "JOIN_MEMBERSHIP", "LEAVE_MEMBERSHIP",
        "MEMBERSHIP_BENEFITS", "MEMBERSHIP_STATUS"
    ],
    # 28.0: Search Insights & Autocomplete
    "SEARCH_INSIGHTS": [
        "AUTOCOMPLETE_SUGGESTIONS", "SEARCH_SUGGESTION_CLICK",
        "POPULAR_SEARCH_TERMS"
    ],
    # 29.0: SEO & Links
    "SEO_LINKS": [
        "REQUEST_SEO_FRIENDLY_URL", "REPORT_BROKEN_LINK"
    ],
    # 30.0: Helpers, Fallbacks & Unknown (excluding UNKNOWN for now)
    "HELPERS_FALLBACK": [
        "HELP_CONTEXTUAL", "HELP_INTENT_EXAMPLE", "BOT_GREETING",
        "BOT_GOODBYE", "BOT_THANKS", "BOT_ERROR", "BOT_CONFIRMATION",
        "BOT_PROMPT_RETRY", "BOT_PROMPT_CONFIRM"
    ],
    # 31.0: Very Fine-Grained Search & User Actions
    "FINE_SEARCH": [
        "SEARCH_CATEGORY_SUB", "SEARCH_BY_COLLECTION", "SEARCH_BY_MATERIAL",
        "SEARCH_BY_THEME", "SEARCH_BY_SEASON", "SEARCH_BY_OCCASION",
        "FILTER_BY_RETURNABLE", "FILTER_BY_FREE_SHIPPING", "FILTER_BY_EXCHANGE"
    ],
    # 32.0: Cart & Checkout Edge Cases
    "CART_EDGE_CASES": [
        "RESOLVE_CART_CONFLICT", "MERGE_CARTS", "SAVE_CART",
        "RESTORE_SAVED_CART", "PRICING_DISCREPANCY", "APPLY_AUTO_DISCOUNT"
    ],
    # 33.0: Order Subscriptions & Recurring
    "ORDER_SUBSCRIPTIONS": [
        "SUBSCRIBE_PRODUCT", "UNSUBSCRIBE_PRODUCT", "SUBSCRIPTION_STATUS",
        "MANAGE_SUBSCRIPTION", "PAUSE_SUBSCRIPTION", "RESUME_SUBSCRIPTION"
    ],
    # 34.0: Security & Fraud
    "SECURITY_FRAUD": [
        "REPORT_FRAUD", "FRAUD_DETECTION_HELP", "LOCK_ACCOUNT", "UNLOCK_ACCOUNT"
    ],
    # 35.0: Data, Exports & Backups
    "DATA_BACKUPS": [
        "EXPORT_ORDERS", "EXPORT_CUSTOMERS", "EXPORT_PRODUCTS",
        "BACKUP_DATA", "RESTORE_DATA"
    ],
    # 36.0: Personal Shopping Assistant
    "SHOPPING_ASSISTANT": [
        "ASSISTANT_PROFILE_SETUP", "ASSISTANT_SAVE_PREFERENCES",
        "ASSISTANT_SUGGEST", "ASSISTANT_REMINDER"
    ],
    # 37.0: Internationalization & Tax
    "TAX_INTERNATIONAL": [
        "CHECK_TAX", "VIEW_TAX_DETAILS", "SET_TAX_RESIDENCE",
        "CHECK_IMPORT_DUTY"
    ],
    # 38.0: Payments — Advanced
    "PAYMENTS_ADVANCED": [
        "SPLIT_PAYMENT", "EMI_OPTIONS", "APPLY_EMI", "CANCEL_EMI",
        "VERIFY_BANK_ACCOUNT"
    ],
    # 39.0: Offline Messaging & Notifications
    "OFFLINE_NOTIFICATIONS": [
        "SCHEDULE_NOTIFICATION", "CANCEL_NOTIFICATION",
        "VIEW_NOTIFICATION_HISTORY"
    ],
    # 40.0: Product Lifecycle
    "PRODUCT_LIFECYCLE": [
        "PRODUCT_UPLOAD", "PRODUCT_UPDATE", "PRODUCT_DELETE",
        "PRODUCT_ARCHIVE", "PRODUCT_RESTORE"
    ],
    # 41.0: Coupons & Vouchers
    "COUPONS_VOUCHERS": [
        "CREATE_COUPON", "EDIT_COUPON", "DELETE_COUPON",
        "VALIDATE_COUPON", "CHECK_COUPON_STATUS"
    ],
    # 42.0: Feedback & Surveys
    "FEEDBACK_SURVEYS": [
        "SUBMIT_SURVEY", "VIEW_SURVEY_RESULTS", "REQUEST_FEEDBACK"
    ],
    # 43.0: Device & App
    "DEVICE_APP": [
        "REPORT_APP_ISSUE", "APP_FEEDBACK", "CHECK_APP_VERSION",
        "REPORT_CRASH"
    ],
    # 44.0: Content, Blog & Guides
    "CONTENT_GUIDES": [
        "VIEW_BLOG", "SEARCH_BLOG", "SUBMIT_BLOG_COMMENT", "VIEW_GUIDE"
    ],
    # 45.0: Cooperative & Social Features
    "SOCIAL_FEATURES": [
        "SHARE_WISHLIST", "FOLLOW_BRAND", "UNFOLLOW_BRAND", "INVITE_FRIEND",
        "APPLY_REFERRAL", "VIEW_REFERRAL_STATUS"
    ],
    # 46.0: Billing & Accounting
    "BILLING_ACCOUNTING": [
        "VIEW_BILLING_HISTORY", "UPDATE_BILLING_INFO", "DOWNLOAD_BILL"
    ],
    # 47.0: QA, Test & DevOps
    "QA_DEVOPS": [
        "TRIGGER_SMOKE_TEST", "TRIGGER_LOAD_TEST", "DEPLOY_ROLLBACK",
        "VIEW_DEPLOYMENT_STATUS"
    ],
    # 48.0: Assortment & Inventory
    "INVENTORY": [
        "VIEW_INVENTORY_LEVELS", "UPDATE_INVENTORY", "REPORT_STOCK_ISSUE",
        "INVENTORY_RECONCILE"
    ],
    # 49.0: Help & Guidance
    "GUIDANCE": [
        "GET_START_GUIDE", "GET_RETURN_INSTRUCTIONS",
        "GET_WARRANTY_INSTRUCTIONS"
    ],
    # 50.0: Miscellaneous Very Fine-Grained
    "MISCELLANEOUS": [
        "PING", "HEALTH_CHECK", "USER_SESSION_INFO", "TIMEZONE_SET",
        "LOCALE_SET"
    ],
    # Final Fallback
    "UNKNOWN": ["UNKNOWN"]
}

#---------- sample intent definition to be added to each file --------------
#
# "track_order": IntentDefinition(
#         category=IntentCategory.TRACK_ORDER,
#         action_code=ActionCode.TRACK_ORDER_STATUS,
#         description="User wants to track the status of an order",
#         example_phrases=[
#             "Where is my order?",
#             "Track my package",
#             "Order status",
#             "When will it arrive?",
#             "Shipping status"
#         ],
#         required_entities=[EntityType.ORDER_ID],
#         optional_entities=[],
#         confidence_threshold=0.8,
#         priority=IntentPriority.HIGH
#     )

#--------------------- end of populate intent definitions -----------------------------