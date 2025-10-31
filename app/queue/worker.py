import time
from app.queue.queue_manager import queue_manager

def llm_worker():
    print(" LLM worker started...")
    while True:
        msg = queue_manager.dequeue_ambiguous_query(timeout=5)
        if msg:
            print(f"Processing: {msg['message_id']} | Query: {msg['query']}")
            # simulate processing
            time.sleep(2)
            queue_manager.enqueue_classification_result(
                message_id=msg["message_id"],
                result={"intent": "TRACK_ORDER", "confidence": 0.94},
                processing_time=2.0
            )

if __name__ == "__main__":
    llm_worker()
