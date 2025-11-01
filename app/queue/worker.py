"""
LLM Worker (CNS-21)

Processes ambiguous queries from the queue using LLM intent classification.
This worker should be run as a separate process/container for async processing.
"""

import time
import logging
from typing import Optional, Dict, Any
from loguru import logger

from app.queue.queue_manager import queue_manager
from app.queue.monitor import queue_monitor
from app.ai.llm_intent.request_handler import RequestHandler
from app.schemas.llm_intent import LLMIntentRequest

# Import status store (TASK-16)
try:
    from app.core.status_store import status_store
    from app.schemas.request_status import ResultSchema
    STATUS_STORE_AVAILABLE = True
except ImportError:
    status_store = None
    STATUS_STORE_AVAILABLE = False

# Initialize LLM handler
try:
    from app.ai.llm_intent.openai_client import OpenAIClient
    import os
    
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        llm_client = OpenAIClient(api_key=api_key)
        llm_handler = RequestHandler(client=llm_client)
        LLM_AVAILABLE = True
    else:
        logger.warning("⚠️ OPENAI_API_KEY not set, LLM processing disabled")
        llm_handler = None
        LLM_AVAILABLE = False
except Exception as e:
    logger.warning(f"⚠️ LLM handler initialization failed: {e}")
    llm_handler = None
    LLM_AVAILABLE = False


def process_message(message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process a single ambiguous query message using LLM.
    
    Args:
        message: Queue message with query and context
    
    Returns:
        Classification result or None if processing failed
    """
    if not LLM_AVAILABLE or llm_handler is None:
        logger.error("❌ LLM handler not available, cannot process message")
        return None
    
    # Handle both TASK-15 format (user_query) and legacy format (query)
    query = message.get("user_query") or message.get("query", "")
    context = message.get("_context") or message.get("context", {})
    
    try:
        # Build LLM request
        llm_request = LLMIntentRequest(
            user_input=query,
            rule_intent=context.get("possible_intents", {}),
            action_code=None,
            top_confidence=0.0,
            next_best_confidence=0.0,
            is_fallback=True
        )
        
        # Process with LLM
        start_time = time.time()
        result = llm_handler.handle(llm_request)
        processing_time = time.time() - start_time
        
        # Record metrics
        queue_monitor.record_dequeue()
        queue_monitor.record_processing_time(processing_time)
        
        logger.info(
            f"✅ Processed message {message['message_id']} | "
            f"Intent: {result.get('action_code')} | "
            f"Confidence: {result.get('confidence', 0.0):.2f} | "
            f"Time: {processing_time:.2f}s"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to process message {message.get('message_id')}: {e}")
        queue_monitor.record_failure()
        return None


def llm_worker(poll_interval: int = 5, max_iterations: Optional[int] = None):
    """
    Main worker loop that processes messages from the queue.
    
    Args:
        poll_interval: Seconds to wait between queue polls
        max_iterations: Maximum number of iterations (None = infinite)
    """
    if queue_manager is None or not queue_manager.is_available():
        logger.error("❌ Queue manager not available, worker cannot start")
        return
    
    if not LLM_AVAILABLE:
        logger.error("❌ LLM handler not available, worker cannot start")
        return
    
    logger.info("🚀 LLM worker started...")
    iteration = 0
    
    try:
        while True:
            if max_iterations and iteration >= max_iterations:
                logger.info(f"✅ Worker completed {max_iterations} iterations")
                break
            
            iteration += 1
            
            # Get next message from queue
            message = queue_manager.dequeue_ambiguous_query(timeout=poll_interval)
            
            if message:
                message_id = message.get("message_id", "unknown")
                logger.info(f"📨 Processing message: {message_id} | Query: '{message.get('query', '')}'")
                
                # Update status to PROCESSING (TASK-16)
                if STATUS_STORE_AVAILABLE and status_store:
                    try:
                        status_store.update_status(message_id, "PROCESSING")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to update status to PROCESSING: {e}")
                
                # Process message
                result = process_message(message)
                
                if result:
                    # Apply confidence calibration (TASK-17)
                    original_confidence = result.get("confidence", 0.0)
                    calibrated_confidence = original_confidence
                    
                    try:
                        from app.ai.llm_intent.confidence_calibration import get_calibrator
                        calibrator = get_calibrator()
                        calibrated_confidence = calibrator.calibrate_confidence(
                            action_code=result.get("action_code"),
                            reported_confidence=original_confidence
                        )
                        result["confidence"] = calibrated_confidence
                        if "metadata" not in result:
                            result["metadata"] = {}
                        result["metadata"]["original_confidence"] = original_confidence
                        result["metadata"]["calibrated_confidence"] = calibrated_confidence
                        
                        if abs(calibrated_confidence - original_confidence) > 0.05:
                            logger.info(
                                f"📊 Calibrated confidence: {original_confidence:.2f} → {calibrated_confidence:.2f} | "
                                f"action_code={result.get('action_code')}"
                            )
                    except Exception as e:
                        logger.warning(f"⚠️ Confidence calibration failed: {e}")
                    
                    # Update status to COMPLETED (TASK-16)
                    if STATUS_STORE_AVAILABLE and status_store:
                        try:
                            result_schema = ResultSchema(
                                action_code=result.get("action_code"),
                                confidence=calibrated_confidence,  # Use calibrated confidence
                                entities=result.get("metadata", {}).get("entities_extracted", {})
                            )
                            status_store.complete_request(message_id, result=result_schema)
                        except Exception as e:
                            logger.warning(f"⚠️ Failed to update status to COMPLETED: {e}")
                    
                    # Enqueue result
                    success = queue_manager.enqueue_classification_result(
                        message_id=message_id,
                        result=result,
                        processing_time=result.get("metadata", {}).get("processing_time_ms", 0) / 1000.0
                    )
                    
                    if not success:
                        logger.warning(f"⚠️ Failed to enqueue result for {message_id}")
                else:
                    # Processing failed, update status to FAILED (TASK-16)
                    if STATUS_STORE_AVAILABLE and status_store:
                        try:
                            error = {"type": "LLM_PROCESSING_ERROR", "message": "LLM processing failed"}
                            status_store.fail_request(message_id, error)
                        except Exception as e:
                            logger.warning(f"⚠️ Failed to update status to FAILED: {e}")
                    
                    # Retry or move to DLQ
                    if not queue_manager.retry_message(message):
                        queue_manager.move_to_dead_letter_queue(
                            message=message,
                            error="LLM processing failed"
                        )
            else:
                # No message, continue polling
                logger.debug(f"No messages in queue, continuing to poll...")
                
    except KeyboardInterrupt:
        logger.info("🛑 Worker stopped by user")
    except Exception as e:
        logger.error(f"❌ Worker error: {e}")
        raise


if __name__ == "__main__":
    # Run worker with default settings
    llm_worker()
