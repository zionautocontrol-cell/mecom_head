from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "mecom_head.db"
HOST = "0.0.0.0"
PORT = 8000

# accept all site IDs (no authentication for now)
TRUSTED_API_KEYS = {}
