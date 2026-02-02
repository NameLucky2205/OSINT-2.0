"""
PeopleFinder - OSINT Backend API
FastAPI приложение с реальными OSINT инструментами
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict
import os
import uuid
import shutil
from pathlib import Path
import asyncio
import re

# Импорт OSINT модулей
from modules.email_checker import check_email_comprehensive
from modules.username_checker import check_username_full
from modules.photo_search import search_by_photo_advanced

# Старые модули (для обратной совместимости)
from modules.sherlock_search import search_by_text
from modules.image_search import search_by_image
import config


# ============================================
# FastAPI Application
# ============================================

app = FastAPI(
    title="PeopleFinder OSINT API",
    description="Профессиональный OSINT API для поиска людей по фото, email и username",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS + ["*"],  # Разрешаем все для dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтирование статических файлов
frontend_path = config.BASE_DIR / "frontend"
if frontend_path.exists():
    js_path = frontend_path / "js"
    if js_path.exists():
        app.mount("/js", StaticFiles(directory=str(js_path)), name="js")
    css_path = frontend_path / "css"
    if css_path.exists():
        app.mount("/css", StaticFiles(directory=str(css_path)), name="css")


# ============================================
# Pydantic Models
# ============================================

class EmailCheckRequest(BaseModel):
    email: str
    check_breaches: bool = True
    check_registrations: bool = True

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Simple email validation"""
        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', v):
            raise ValueError('Invalid email format')
        return v


class UsernameCheckRequest(BaseModel):
    username: str
    max_sites: Optional[int] = 20
    extract_metadata: bool = True


class OSINTResponse(BaseModel):
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None


# ============================================
# Utility Functions
# ============================================

def save_upload_file(upload_file: UploadFile) -> str:
    """Сохранение загруженного файла"""
    file_extension = os.path.splitext(upload_file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = config.UPLOAD_DIR / unique_filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    return str(file_path)


def validate_image(file: UploadFile) -> bool:
    """Валидация изображения"""
    file_extension = os.path.splitext(file.filename)[1].lower().replace(".", "")
    if file_extension not in config.ALLOWED_EXTENSIONS:
        return False

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > config.MAX_UPLOAD_SIZE:
        return False

    return True


def cleanup_file(file_path: str):
    """Фоновая очистка файла"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except:
        pass


# ============================================
# Frontend Routes
# ============================================

@app.get("/")
async def root():
    """Главная страница"""
    index_file = frontend_path / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "PeopleFinder OSINT API", "version": "2.0.0", "docs": "/docs"}


@app.get("/osint")
async def osint_panel():
    """OSINT Analytics Panel"""
    panel_file = frontend_path / "osint-panel.html"
    if panel_file.exists():
        return FileResponse(str(panel_file))
    return {"error": "OSINT panel not found"}


@app.get("/debug.html")
async def debug_page():
    """Debug страница"""
    debug_file = frontend_path / "debug.html"
    if debug_file.exists():
        return FileResponse(str(debug_file))
    return {"error": "Debug page not found"}


# ============================================
# API Health & Info
# ============================================

@app.get("/api/health")
async def health_check():
    """Проверка работоспособности API"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "services": {
            "email_checker": "operational",
            "username_checker": "operational",
            "photo_search": "operational"
        },
        "osint_tools": {
            "holehe": "integrated",
            "haveibeenpwned": "integrated",
            "maigret_logic": "integrated",
            "yandex_images": "integrated",
            "google_images": "integrated",
            "tineye": "integrated"
        }
    }


@app.get("/api/info")
async def api_info():
    """Информация об API и доступных методах"""
    return {
        "name": "PeopleFinder OSINT API",
        "version": "2.0.0",
        "description": "Профессиональный OSINT инструмент для поиска людей",
        "endpoints": {
            "email": "/api/osint/email - Глубокая проверка email (утечки + регистрации)",
            "username": "/api/osint/username - Поиск по username на 20+ платформах",
            "photo": "/api/osint/photo - Reverse image search (Yandex + Google + TinEye)",
            "legacy_text": "/api/search/text - Старый метод поиска по тексту",
            "legacy_image": "/api/search/image - Старый метод поиска по фото"
        },
        "features": [
            "HaveIBeenPwned integration для проверки утечек",
            "Holehe-подобная проверка регистраций email",
            "Maigret-подобный поиск по username с извлечением метаданных",
            "Yandex Images reverse search для РФ профилей",
            "Google Images и TinEye integration",
            "Извлечение социальных профилей из результатов",
            "Асинхронная обработка для максимальной скорости"
        ]
    }


# ============================================
# OSINT ENDPOINTS (Новые продвинутые)
# ============================================

@app.post("/api/osint/email")
async def check_email_osint(request: EmailCheckRequest):
    """
    🔥 OSINT проверка email адреса

    Функции:
    - Проверка утечек через HaveIBeenPwned
    - Проверка регистраций на популярных сайтах (holehe logic)
    - Извлечение метаданных (провайдер, MX записи)
    - Определение одноразовых email

    Args:
        request: EmailCheckRequest с параметрами

    Returns:
        Полный отчёт по email
    """
    import time
    start_time = time.time()

    try:
        # Запускаем полную проверку
        result = await check_email_comprehensive(request.email)

        processing_time = time.time() - start_time

        return {
            "success": result.get("success", True),
            "email": request.email,
            "data": result,
            "processing_time": round(processing_time, 2),
            "timestamp": int(time.time())
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при проверке email: {str(e)}")


@app.post("/api/osint/username")
async def check_username_osint(request: UsernameCheckRequest):
    """
    🔥 OSINT поиск по username

    Функции:
    - Проверка на 20+ популярных платформах
    - Извлечение метаданных (имя, аватар, биография)
    - Категоризация по типам платформ
    - Confidence scoring

    Args:
        request: UsernameCheckRequest с параметрами

    Returns:
        Полный отчёт по username
    """
    import time
    start_time = time.time()

    try:
        # Запускаем полную проверку
        result = await check_username_full(request.username, request.max_sites)

        processing_time = time.time() - start_time

        return {
            "success": True,
            "username": request.username,
            "data": result,
            "processing_time": round(processing_time, 2),
            "timestamp": int(time.time())
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при поиске username: {str(e)}")


@app.post("/api/osint/photo")
async def check_photo_osint(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    🔥 OSINT поиск по фотографии

    Функции:
    - Reverse search через Yandex Images (лучший для РФ)
    - Reverse search через Google Images
    - Reverse search через TinEye
    - Извлечение социальных профилей из результатов
    - Автоматическая очистка загруженных файлов

    Args:
        file: Изображение для поиска

    Returns:
        Результаты от всех сервисов + социальные профили
    """
    import time
    start_time = time.time()

    try:
        # Валидация
        if not validate_image(file):
            raise HTTPException(
                status_code=400,
                detail="Недопустимый формат или размер файла"
            )

        # Сохранение
        file_path = save_upload_file(file)

        try:
            # Запускаем поиск
            result = await search_by_photo_advanced(file_path)

            processing_time = time.time() - start_time

            # Планируем удаление файла
            if background_tasks:
                background_tasks.add_task(cleanup_file, file_path)

            return {
                "success": result.get("success", True),
                "filename": file.filename,
                "data": result,
                "processing_time": round(processing_time, 2),
                "timestamp": int(time.time())
            }

        finally:
            # Удаляем файл сразу если background_tasks не используется
            if not background_tasks:
                cleanup_file(file_path)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при поиске по фото: {str(e)}")


# ============================================
# LEGACY ENDPOINTS (для обратной совместимости)
# ============================================

@app.post("/api/search/text")
async def search_text_legacy(
    query: str = Form(...),
    search_type: str = Form("username"),
    max_sites: int = Form(15)
):
    """
    Старый метод поиска по тексту (обратная совместимость)

    Рекомендуется использовать:
    - /api/osint/email для email
    - /api/osint/username для username
    """
    try:
        if search_type == "email":
            # Перенаправляем на новый метод
            result = await check_email_comprehensive(query)
            return {"success": True, "results": [result], "total_found": 1}
        else:
            # Старый метод для username
            result = await search_by_text(query, search_type, max_sites)
            return {
                "success": True,
                "query": query,
                "results": result.get("results", []),
                "total_found": result.get("total_found", 0)
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search/image")
async def search_image_legacy(file: UploadFile = File(...)):
    """
    Старый метод поиска по изображению (обратная совместимость)

    Рекомендуется использовать: /api/osint/photo
    """
    try:
        if not validate_image(file):
            raise HTTPException(status_code=400, detail="Invalid file")

        file_path = save_upload_file(file)

        try:
            result = await search_by_image(file_path)
            return {
                "success": True if not result.get("error") else False,
                "results": result.get("results", []),
                "total_found": result.get("total_found", 0)
            }
        finally:
            cleanup_file(file_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Batch Operations (Пакетная обработка)
# ============================================

@app.post("/api/osint/batch/usernames")
async def batch_check_usernames(usernames: List[str], max_sites: int = 10):
    """
    Пакетная проверка множества usernames

    Args:
        usernames: Список usernames для проверки
        max_sites: Количество сайтов для каждого username

    Returns:
        Результаты по каждому username
    """
    if len(usernames) > 20:
        raise HTTPException(status_code=400, detail="Максимум 20 usernames за раз")

    results = []

    for username in usernames:
        try:
            result = await check_username_full(username, max_sites)
            results.append({
                "username": username,
                "success": True,
                "data": result
            })
        except Exception as e:
            results.append({
                "username": username,
                "success": False,
                "error": str(e)
            })

    return {
        "success": True,
        "total_checked": len(usernames),
        "results": results
    }


# ============================================
# Cleanup & Utilities
# ============================================

@app.delete("/api/cleanup")
async def cleanup_uploads():
    """Очистка загруженных файлов"""
    try:
        deleted_count = 0
        for file in config.UPLOAD_DIR.glob("*"):
            if file.is_file():
                os.remove(file)
                deleted_count += 1

        return {"success": True, "files_deleted": deleted_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Application Startup
# ============================================

if __name__ == "__main__":
    import uvicorn

    print("""
    ╔═══════════════════════════════════════════════════╗
    ║      PeopleFinder OSINT API v2.0                  ║
    ╠═══════════════════════════════════════════════════╣
    ║  URL: http://{}:{}                          ║
    ║  Docs: http://{}:{}/docs                    ║
    ║  ReDoc: http://{}:{}/redoc                  ║
    ╠═══════════════════════════════════════════════════╣
    ║  Endpoints:                                       ║
    ║  • POST /api/osint/email - Email OSINT            ║
    ║  • POST /api/osint/username - Username OSINT      ║
    ║  • POST /api/osint/photo - Photo OSINT            ║
    ╚═══════════════════════════════════════════════════╝
    """.format(
        config.HOST, config.PORT,
        config.HOST, config.PORT,
        config.HOST, config.PORT
    ))

    uvicorn.run(
        "main_osint:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level="info"
    )
