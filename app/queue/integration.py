"""
Queue Integration (CNS-21)

Integrates queue infrastructure with CNS-12 Ambiguity Resolver.
Routes ambiguous/unclear queries to LLM processing queue.
"""

from typing import Dict, Any
from loguru import logger

from app.queue.queue_manager import queue_manager
from app.queue.monitor import queue_monitor
from app.queue.config import queue_config


def send_to_llm_queue(
    query: str,
    ambiguity_result: Dict[str, Any],
    user_id: str = "anonymous",
    is_premium: bool = False
) -> str:
    """
    Send ambiguous/unclear query to LLM processing queue.
    
    This integrates with CNS-12 ambiguity resolver output.
    
    Args:
        query: User's original query
        ambiguity_result: Result from detect_intent() in ambiguity_resolver.py
        user_id: User identifier
        is_premium: Whether user has premium subscription
    
    Returns:
        message_id: Queue message identifier
    
    Example:
        from app.ai.intent_classification.ambiguity_resolver import detect_intent
        
        result = detect_intent("add shoes and track order")
        if result["action"] == "AMBIGUOUS":
            message_id = send_to_llm_queue(
                query="add shoes and track order",
                ambiguity_result=result,
                user_id="user_123"
            )
    """
    # Determine priority
    priority = (
        queue_config.PRIORITY_HIGH if is_premium 
        else queue_config.PRIORITY_NORMAL
    )
    
    # Build context for LLM
    context = {
        "ambiguity_type": ambiguity_result.get("action"),  # AMBIGUOUS or UNCLEAR
        "possible_intents": ambiguity_result.get("possible_intents", {}),
        "confidence_scores": ambiguity_result.get("possible_intents", {}),
        "user_id": user_id,
        "is_premium": is_premium,
        "source": "CNS-12_ambiguity_resolver"
    }
    
    try:
        # Enqueue for LLM processing
        message_id = queue_manager.enqueue_ambiguous_query(
            query=query,
            context=context,
            priority=priority
        )
        
        # Record metrics
        queue_monitor.record_enqueue()
        
        logger.info(
            f"✅ Sent to LLM queue: {message_id} | "
            f"Query: '{query}' | Type: {context['ambiguity_type']}"
        )
        
        return message_id
        
    except Exception as e:
        logger.error(f"❌ Failed to send to LLM queue: {e}")
        queue_monitor.record_failure()
        raise


def get_classification_result(message_id: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Get LLM classification result from output queue.
    
    Args:
        message_id: Message ID to wait for
        timeout: Seconds to wait for result
    
    Returns:
        result: LLM classification result or error
    """
    # This will be implemented when LLM worker is built
    # For now, just a placeholder
    logger.info(f"Waiting for result of message: {message_id}")
    return {"status": "pending", "message_id": message_id}
