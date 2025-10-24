import json
import logging
import os
import sys

from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

# --- Add project root to path ---
# This allows us to import from 'app'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)
# -------------------------------

# Now we can import from our app
try:
    from app.core.config import settings
    from app.core.db import Base, engine, SessionLocal
    from app.models.product import Product  # Assumes you have app/models/product.py
except ImportError as e:
    print(f"Error: Could not import app modules. Make sure your structure is correct.")
    print(f"Details: {e}")
    print(f"Project root added to path: {project_root}")
    sys.exit(1)

# --- Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

QDRANT_COLLECTION_NAME = "products"
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2' # A good, fast starter model

# --- Helper Function ---
def get_product_text_representation(product: dict) -> str:
    """Creates a single string for embedding."""
    return (
        f"Name: {product.get('name', '')}. "
        f"Description: {product.get('description', '')}. "
        f"Category: {product.get('category', '')}."
    )

# --- Main Ingestion Function ---
def main():
    logger.info("Starting data ingestion process...")

    # --- 1. Initialize Clients ---
    try:
        # Load embedding model
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}...")
        model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        
        # Connect to Qdrant
        logger.info(f"Connecting to Qdrant at {settings.QDRANT_URL}...")
        qdrant = QdrantClient(
            url=settings.QDRANT_URL, 
            api_key=settings.QDRANT_API_KEY
        )
        
        # Get database session
        db: Session = SessionLocal()
        
    except Exception as e:
        logger.error(f"Failed to initialize clients: {e}")
        return

    # --- 2. Setup Databases ---
    try:
        logger.info("Setting up database tables...")
        # Create all tables in PostgreSQL (idempotent)
        Base.metadata.create_all(bind=engine)
        
        # Create Qdrant collection
        logger.info(f"Setting up Qdrant collection: {QDRANT_COLLECTION_NAME}...")
        qdrant.recreate_collection(
            collection_name=QDRANT_COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=model.get_sentence_embedding_dimension(),
                distance=models.Distance.COSINE
            )
        )
    except Exception as e:
        logger.error(f"Failed to setup databases: {e}")
        db.close()
        return
        
    # --- 3. Load Data ---
    try:
        data_file_path = os.path.join(project_root, 'products.json')
        logger.info(f"Loading data from {data_file_path}...")
        with open(data_file_path, 'r') as f:
            products_data = json.load(f)
    except FileNotFoundError:
        logger.error(f"FATAL: products.json not found at {data_file_path}.")
        db.close()
        return

    # --- 4. Process and Ingest Data ---
    logger.info(f"Ingesting {len(products_data)} products...")
    
    qdrant_points = []
    sql_products = []
    
    try:
        for i, product_dict in enumerate(products_data):
            # A. Prepare text for embedding
            text_to_embed = get_product_text_representation(product_dict)
            
            # B. Create embedding
            vector = model.encode(text_to_embed).tolist()
            
            # C. Create product for PostgreSQL
            # We save it in a list to add all at once
            db_product = Product(
                name=product_dict['name'],
                description=product_dict['description'],
                price=product_dict['price'],
                category=product_dict.get('category'), # .get() is safer
                image_url=product_dict.get('image_url')
            )
            sql_products.append(db_product)
            
            # D. Prepare product for Qdrant
            # We will link the vector to the SQL ID *after* committing
            qdrant_points.append({
                "id": i, # Temporary ID
                "vector": vector,
                "payload": product_dict # Store the raw data
            })

        # --- 5. Commit to Databases ---
        
        # A. Commit to PostgreSQL first to get the real IDs
        logger.info("Committing to PostgreSQL...")
        db.add_all(sql_products)
        db.commit()
        
        # B. Update Qdrant points with the real SQL IDs
        logger.info("Updating Qdrant points with SQL IDs...")
        updated_points = []
        for i, db_product in enumerate(sql_products):
            qdrant_points[i]['id'] = db_product.id # Use the real SQL ID
            qdrant_points[i]['payload']['sql_id'] = db_product.id
            
            updated_points.append(
                models.PointStruct(
                    id=qdrant_points[i]['id'],
                    vector=qdrant_points[i]['vector'],
                    payload=qdrant_points[i]['payload']
                )
            )

        # C. Commit to Qdrant
        logger.info("Upserting points to Qdrant...")
        qdrant.upsert(
            collection_name=QDRANT_COLLECTION_NAME,
            points=updated_points,
            wait=True # Wait for the operation to complete
        )
        
        logger.info("--- 🚀 Ingestion Complete! ---")
        
    except Exception as e:
        logger.error(f"An error occurred during ingestion: {e}")
        db.rollback() # Roll back any partial SQL changes
    finally:
        db.close()
        logger.info("Database session closed.")


if __name__ == "__main__":
    # This check ensures your .env variables are loaded
    if not settings.DATABASE_URL or not settings.QDRANT_URL:
        logger.error("FATAL: Environment variables not loaded.")
        logger.error("Did you create and fill out your .env file?")
    else:
        main()