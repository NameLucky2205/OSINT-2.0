"""
Конфигурация приложения PeopleFinder
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Базовые пути
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "backend" / "uploads"
STATIC_DIR = BASE_DIR / "backend" / "static"

# Создание директорий если не существуют
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Server settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# Upload settings
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 10485760))  # 10MB
ALLOWED_EXTENSIONS = set(os.getenv("ALLOWED_EXTENSIONS", "jpg,jpeg,png,gif,webp").split(","))

# Search settings
MAX_USERNAME_SITES = int(os.getenv("MAX_USERNAME_SITES", 50))
IMAGE_SEARCH_TIMEOUT = int(os.getenv("IMAGE_SEARCH_TIMEOUT", 30))
USERNAME_SEARCH_TIMEOUT = int(os.getenv("USERNAME_SEARCH_TIMEOUT", 60))

# Face recognition settings
FACE_TOLERANCE = float(os.getenv("FACE_TOLERANCE", 0.6))

# Proxy settings (опционально)
PROXIES = {}
if os.getenv("HTTP_PROXY"):
    PROXIES["http"] = os.getenv("HTTP_PROXY")
if os.getenv("HTTPS_PROXY"):
    PROXIES["https"] = os.getenv("HTTPS_PROXY")

# CORS настройки
CORS_ORIGINS = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
]
