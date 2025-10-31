# test_queue_job.py

from app.queue.queue_manager import queue_manager

if __name__ == "__main__":
    print("🚀 Sending test job to queue...")
    
    # Example of a fake ambiguous query
    query = "Book me a table"
    context = {"user_id": 123, "possible_intents": ["book_restaurant", "book_flight"]}
    
    # Enqueue the message
    msg_id = queue_manager.enqueue_ambiguous_query(query, context)
    print(f"✅ Message enqueued successfully! ID = {msg_id}")
