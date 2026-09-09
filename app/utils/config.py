import os

from dotenv import load_dotenv


load_dotenv()


API_KEY = os.getenv("API_KEY", "")
BASE_URL = os.getenv("BASE_URL", "")
MODEL_NAME = os.getenv("MODEL_NAME", "")

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
DB_PATH = os.getenv("DB_PATH", "./data/chroma_db")

EMBEDDING_MODEL_PATH = os.getenv(
    "EMBEDDING_MODEL_PATH",
    "",
)

ENABLE_LLM = os.getenv("ENABLE_LLM", "true").lower() == "true"
MAX_LLM_TOKENS = int(os.getenv("MAX_LLM_TOKENS", "500"))