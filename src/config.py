import os
from dotenv import load_dotenv

# Charge les variables d'environnement (.env)
load_dotenv(override=True)

INPUT_DIR = "data/main/raw"
MD_DIR = "data/main/intermediate"
CHUNKS_JSON = "data/main/processed/all_chunks.json"
DB_PATH = "./db_multi_docs"

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(MD_DIR, exist_ok=True)
os.makedirs("data/main/processed", exist_ok=True)

SERVER = "http://localhost:11434"
MODEL = "mistral"
EMBEDDING_MODEL = "nomic-embed-text"

LLAMA_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")
os.environ["LLAMA_CLOUD_API_KEY"] = LLAMA_API_KEY