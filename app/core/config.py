from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    # Load .env file from the project root
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), '..', '..', '.env'),
        env_file_encoding='utf-8',
        extra='ignore'
    )

    # --- Database ---
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/chatnShop"

    # --- Qdrant ---
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None

    # --- OpenAI ---
    OPENAI_API_KEY: str | None = None

# Create a single instance to be imported by other modules
settings = Settings()

# --- Test loaded settings (optional, for debugging) ---
if __name__ == "__main__":
    print("--- Loaded Settings ---")
    print(f"DATABASE_URL: {settings.DATABASE_URL}")
    print(f"QDRANT_URL: {settings.QDRANT_URL}")
    print(f"OPENAI_API_KEY: {settings.OPENAI_API_KEY[:4]}...")
    print("-----------------------")