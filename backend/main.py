"""
PeopleFinder - Backend API
FastAPI приложение для поиска людей по фото и текстовым данным
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import uuid
import shutil
from pathlib import Path

# Импорт наших модулей
from modules.sherlock_search import search_by_text
from modules.image_search import search_by_image
import config


# Инициализация FastAPI
app = FastAPI(
    title="PeopleFinder API",
    description="API для поиска людей по фотографии или username/email",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтирование статических файлов
frontend_path = config.BASE_DIR / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")


# Pydantic модели
class TextSearchRequest(BaseModel):
    query: str
    search_type: str = "username"  # username или email
    max_sites: Optional[int] = 15


class SearchResponse(BaseModel):
    success: bool
    query: Optional[str] = None
    results: List[dict]
    total_found: int
    message: Optional[str] = None


# Утилиты
def save_upload_file(upload_file: UploadFile) -> str:
    """
    Сохранение загруженного файла

    Args:
        upload_file: загруженный файл

    Returns:
        Путь к сохраненному файлу
    """
    # Генерация уникального имени
    file_extension = os.path.splitext(upload_file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = config.UPLOAD_DIR / unique_filename

    # Сохранение файла
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    return str(file_path)


def validate_image(file: UploadFile) -> bool:
    """
    Валидация изображения

    Args:
        file: загруженный файл

    Returns:
        True если файл валидный
    """
    # Проверка расширения
    file_extension = os.path.splitext(file.filename)[1].lower().replace(".", "")
    if file_extension not in config.ALLOWED_EXTENSIONS:
        return False

    # Проверка размера
    file.file.seek(0, 2)  # Переход в конец файла
    file_size = file.file.tell()
    file.file.seek(0)  # Возврат в начало

    if file_size > config.MAX_UPLOAD_SIZE:
        return False

    return True


# API Endpoints

@app.get("/")
async def root():
    """Главная страница - возврат frontend"""
    index_file = frontend_path / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "PeopleFinder API running", "version": "1.0.0"}


@app.get("/api/health")
async def health_check():
    """Проверка работоспособности API"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "text_search": "operational",
            "image_search": "operational"
        }
    }


@app.post("/api/search/text", response_model=SearchResponse)
async def search_text(request: TextSearchRequest):
    """
    Поиск по текстовым данным (username или email)

    Args:
        request: запрос с параметрами поиска

    Returns:
        SearchResponse с результатами
    """
    try:
        # Валидация
        if not request.query or len(request.query) < 3:
            raise HTTPException(
                status_code=400,
                detail="Запрос должен содержать минимум 3 символа"
            )

        # Поиск
        results = await search_by_text(
            query=request.query,
            search_type=request.search_type,
            max_sites=request.max_sites
        )

        return SearchResponse(
            success=True,
            query=request.query,
            results=results.get("results", []),
            total_found=results.get("total_found", 0),
            message=f"Поиск завершен. Найдено результатов: {results.get('total_found', 0)}"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при поиске: {str(e)}")


@app.post("/api/search/image", response_model=SearchResponse)
async def search_image(file: UploadFile = File(...)):
    """
    Поиск по изображению

    Args:
        file: загруженное изображение

    Returns:
        SearchResponse с результатами
    """
    try:
        # Валидация файла
        if not validate_image(file):
            raise HTTPException(
                status_code=400,
                detail="Недопустимый формат или размер файла. Разрешены: jpg, jpeg, png, gif, webp. Максимум 10MB."
            )

        # Сохранение файла
        file_path = save_upload_file(file)

        try:
            # Поиск
            results = await search_by_image(file_path)

            # Проверка на ошибки
            if "error" in results:
                return SearchResponse(
                    success=False,
                    results=[],
                    total_found=0,
                    message=results["error"]
                )

            return SearchResponse(
                success=True,
                query=file.filename,
                results=results.get("results", []),
                total_found=results.get("total_found", 0),
                message=f"Поиск завершен. Обнаружено лиц: {results.get('faces_detected', 0)}. Найдено результатов: {results.get('total_found', 0)}"
            )

        finally:
            # Удаление файла после обработки
            if os.path.exists(file_path):
                os.remove(file_path)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при поиске: {str(e)}")


@app.post("/api/search/combined")
async def search_combined(
    file: Optional[UploadFile] = File(None),
    query: Optional[str] = Form(None),
    search_type: str = Form("username")
):
    """
    Комбинированный поиск (и по фото, и по тексту)

    Args:
        file: опциональное изображение
        query: опциональный текстовый запрос
        search_type: тип текстового поиска

    Returns:
        Объединенные результаты
    """
    results = {
        "success": True,
        "image_results": [],
        "text_results": [],
        "total_found": 0
    }

    try:
        # Поиск по изображению
        if file:
            if not validate_image(file):
                raise HTTPException(
                    status_code=400,
                    detail="Недопустимый формат изображения"
                )

            file_path = save_upload_file(file)
            try:
                image_results = await search_by_image(file_path)
                results["image_results"] = image_results.get("results", [])
                results["faces_detected"] = image_results.get("faces_detected", 0)
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)

        # Поиск по тексту
        if query and len(query) >= 3:
            text_results = await search_by_text(query, search_type, 15)
            results["text_results"] = text_results.get("results", [])

        # Подсчет общего количества
        results["total_found"] = len(results["image_results"]) + len(results["text_results"])

        return results

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при комбинированном поиске: {str(e)}")


@app.delete("/api/cleanup")
async def cleanup_uploads():
    """Очистка старых загруженных файлов"""
    try:
        deleted_count = 0
        for file in config.UPLOAD_DIR.glob("*"):
            if file.is_file():
                os.remove(file)
                deleted_count += 1

        return {
            "success": True,
            "message": f"Удалено файлов: {deleted_count}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при очистке: {str(e)}")


# Запуск приложения
if __name__ == "__main__":
    import uvicorn

    print(f"""
    ╔═══════════════════════════════════════╗
    ║       PeopleFinder API Server         ║
    ╠═══════════════════════════════════════╣
    ║  URL: http://{config.HOST}:{config.PORT}       ║
    ║  Docs: http://{config.HOST}:{config.PORT}/docs ║
    ╚═══════════════════════════════════════╝
    """)

    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level="info"
    )
