from ..models import IntentDefinition
from ..enums import IntentCategory, ActionCode, IntentPriority, EntityType

account_profile_intent_definitions = {
    # 6.0 Account, Auth & Profile
    "create_account": IntentDefinition(
        category=IntentCategory.ACCOUNT_PROFILE,
        action_code=ActionCode.CREATE_ACCOUNT,
        description="User wants to create a new account",
        example_phrases=[
            "I want to create an account",
            "Sign up",
            "Create account",
            "Register",
            "New account",
            "I want to register",
            "Create new account",
            "Sign me up"
        ],
        required_entities=[],
        optional_entities=[EntityType.EMAIL, EntityType.PHONE_NUMBER],
        confidence_threshold=0.90,
        priority=IntentPriority.CRITICAL
    ),

    "login": IntentDefinition(
        category=IntentCategory.ACCOUNT_PROFILE,
        action_code=ActionCode.LOGIN,
        description="User wants to log into their account",
        example_phrases=[
            "I want to login",
            "Sign in",
            "Login",
            "Log me in",
            "Access my account",
            "Sign into account",
            "Login to account",
            "I want to sign in"
        ],
        required_entities=[],
        optional_entities=[EntityType.EMAIL, EntityType.USER_ID],
        confidence_threshold=0.90,
        priority=IntentPriority.CRITICAL
    ),

    "logout": IntentDefinition(
        category=IntentCategory.ACCOUNT_PROFILE,
        action_code=ActionCode.LOGOUT,
        description="User wants to log out of their account",
        example_phrases=[
            "I want to logout",
            "Sign out",
            "Logout",
            "Log me out",
            "Sign out of account",
            "Logout of account",
            "End session",
            "I want to sign out"
        ],
        required_entities=[],
        optional_entities=[],
        confidence_threshold=0.90,
        priority=IntentPriority.MEDIUM
    ),


    "forgot_password": IntentDefinition(
        category=IntentCategory.ACCOUNT_PROFILE,
        action_code=ActionCode.FORGOT_PASSWORD,
        description="User wants to reset their forgotten password",
        example_phrases=[
            "I forgot my password",
            "Reset password",
            "Forgot password",
            "Password reset",
            "I can't remember password",
            "Reset my password",
            "Forgot my password",
            "Password help"
        ],
        required_entities=[],
        optional_entities=[EntityType.EMAIL],
        confidence_threshold=0.90,
        priority=IntentPriority.CRITICAL
    ),

    "reset_password": IntentDefinition(
        category=IntentCategory.ACCOUNT_PROFILE,
        action_code=ActionCode.RESET_PASSWORD,
        description="User wants to reset their password",
        example_phrases=[
            "Reset my password",
            "Change password",
            "New password",
            "Update password",
            "Reset password",
            "Change my password",
            "Update my password",
            "Set new password"
        ],
        required_entities=[],
        optional_entities=[],
        confidence_threshold=0.85,
        priority=IntentPriority.CRITICAL
    ),

    "update_profile": IntentDefinition(
        category=IntentCategory.ACCOUNT_PROFILE,
        action_code=ActionCode.UPDATE_PROFILE,
        description="User wants to update their profile information",
        example_phrases=[
            "Update my profile",
            "Change profile",
            "Edit profile",
            "Modify profile",
            "Update profile info",
            "Change my profile",
            "Edit my profile",
            "Update account info"
        ],
        required_entities=[],
        optional_entities=[EntityType.EMAIL, EntityType.PHONE_NUMBER, EntityType.ADDRESS],
        confidence_threshold=0.85,
        priority=IntentPriority.HIGH
    ),

    "view_profile": IntentDefinition(
        category=IntentCategory.ACCOUNT_PROFILE,
        action_code=ActionCode.VIEW_PROFILE,
        description="User wants to view their profile information",
        example_phrases=[
            "Show my profile",
            "View profile",
            "See my profile",
            "Display profile",
            "Show profile info",
            "View my account",
            "See account info",
            "Show my details"
        ],
        required_entities=[],
        optional_entities=[],
        confidence_threshold=0.85,
        priority=IntentPriority.MEDIUM
    ),

    "delete_account": IntentDefinition(
        category=IntentCategory.ACCOUNT_PROFILE,
        action_code=ActionCode.DELETE_ACCOUNT,
        description="User wants to delete their account",
        example_phrases=[
            "Delete my account",
            "Close account",
            "Remove account",
            "Delete account",
            "Close my account",
            "Remove my account",
            "Cancel account",
            "Terminate account"
        ],
        required_entities=[],
        optional_entities=[EntityType.REASON],
        confidence_threshold=0.90,
        priority=IntentPriority.CRITICAL
    ),

    
}