from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    ORACLE_DSN = os.getenv("ORACLE_DSN", "localhost/XEPDB1")
    ORACLE_USER = os.getenv("ORACLE_USER", "users")
    ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "oracle")
    EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    TOPK = int(os.getenv("TOPK", "200"))
    THRESHOLD = float(os.getenv("THRESHOLD", "0.82"))
    VECTOR_DIM = 512  # keep in sync with DB schema
    POOL_MIN = int(os.getenv("POOL_MIN", "1"))
    POOL_MAX = int(os.getenv("POOL_MAX", "4"))
    POOL_INC = int(os.getenv("POOL_INC", "1"))
