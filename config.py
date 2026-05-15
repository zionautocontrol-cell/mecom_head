import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "mecom_head.db"
HOST = os.getenv("MECOM_HEAD_HOST", "0.0.0.0")
PORT = int(os.getenv("MECOM_HEAD_PORT", "8000"))

# API key authentication
# Format: {"site_id": "api_key"}
# If empty, all requests are accepted (insecure mode)
TRUSTED_API_KEYS = {
    k.split("=")[0].strip(): k.split("=")[1].strip()
    for k in os.getenv("MECOM_TRUSTED_KEYS", "").split(",")
    if "=" in k
}

# Admin credentials for dashboard
ADMIN_USERNAME = os.getenv("MECOM_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("MECOM_ADMIN_PASS", "admin123")
