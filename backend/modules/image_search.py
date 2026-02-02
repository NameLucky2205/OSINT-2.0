"""
Модуль поиска по изображению (Reverse Image Search)
Использует Google Images, Yandex Images и TinEye
"""
import os
import requests
import asyncio
import aiohttp
from typing import List, Dict, Optional
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import quote, urlencode
# import face_recognition
# import numpy as np
from PIL import Image
import io


class ReverseImageSearch:
    """Класс для поиска по изображению через различные сервисы"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

    def extract_faces(self, image_path: str) -> List:
        """
        Извлечение лиц из изображения (заглушка без face_recognition)

        Args:
            image_path: путь к изображению

        Returns:
            List кодировок лиц
        """
        # TODO: Установите face_recognition для полной функциональности
        # pip install dlib face-recognition
        return []

    def compare_faces(self, known_face_encoding, image_to_check: str, tolerance: float = 0.6) -> bool:
        """
        Сравнение лиц (заглушка без face_recognition)

        Args:
            known_face_encoding: эталонная кодировка лица
            image_to_check: путь к изображению для проверки
            tolerance: порог совпадения (0.0-1.0)

        Returns:
            True если лица совпадают
        """
        # TODO: Установите face_recognition для полной функциональности
        return False

    async def search_google_images(self, image_path: str) -> List[Dict]:
        """
        Поиск через Google Images (упрощенная версия)

        Args:
            image_path: путь к изображению

        Returns:
            List найденных результатов
        """
        results = []

        try:
            # Google Lens API (неофициальный метод через SerpAPI-подобный подход)
            # Для production лучше использовать официальные API или сервисы

            # Читаем изображение
            with open(image_path, 'rb') as f:
                image_data = f.read()

            # Формируем URL для Google Images Search
            # Используем метод upload через форму
            search_url = "https://www.google.com/searchbyimage/upload"

            files = {'encoded_image': ('image.jpg', image_data, 'image/jpeg')}
            data = {'image_content': ''}

            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(search_url, data=data, headers=self.headers, timeout=15) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')

                            # Парсинг результатов (упрощенный)
                            # В реальности нужен более сложный парсинг
                            links = soup.find_all('a', href=True)

                            for link in links[:10]:  # Берем первые 10 ссылок
                                href = link.get('href', '')
                                if 'http' in href and 'google' not in href:
                                    results.append({
                                        "source": "Google Images",
                                        "url": href,
                                        "title": link.get_text(strip=True)[:100],
                                        "confidence": 0.7
                                    })
                except Exception as e:
                    print(f"Ошибка Google Images: {e}")

        except Exception as e:
            print(f"Ошибка при поиске в Google Images: {e}")

        return results

    async def search_yandex_images(self, image_path: str) -> List[Dict]:
        """
        Поиск через Yandex Images

        Args:
            image_path: путь к изображению

        Returns:
            List найденных результатов
        """
        results = []

        try:
            # Yandex Images upload URL
            upload_url = "https://yandex.com/images/search"

            with open(image_path, 'rb') as f:
                image_data = f.read()

            files = {'upfile': ('image.jpg', image_data, 'image/jpeg')}

            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(upload_url, data=files, headers=self.headers, timeout=15) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')

                            # Парсинг результатов Yandex
                            items = soup.find_all('div', class_='serp-item')

                            for item in items[:10]:
                                link = item.find('a', href=True)
                                if link:
                                    results.append({
                                        "source": "Yandex Images",
                                        "url": link['href'],
                                        "title": link.get('title', 'No title')[:100],
                                        "confidence": 0.7
                                    })
                except Exception as e:
                    print(f"Ошибка Yandex Images: {e}")

        except Exception as e:
            print(f"Ошибка при поиске в Yandex: {e}")

        return results

    async def search_tineye(self, image_path: str) -> List[Dict]:
        """
        Поиск через TinEye (упрощенная версия)

        Args:
            image_path: путь к изображению

        Returns:
            List найденных результатов
        """
        results = []

        try:
            # TinEye API требует регистрации
            # Здесь упрощенная версия через веб-интерфейс

            with open(image_path, 'rb') as f:
                image_data = f.read()

            upload_url = "https://tineye.com/search"

            files = {'image': ('image.jpg', image_data, 'image/jpeg')}

            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(upload_url, data=files, headers=self.headers, timeout=15) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')

                            # Парсинг результатов TinEye
                            matches = soup.find_all('div', class_='match')

                            for match in matches[:10]:
                                link = match.find('a', href=True)
                                if link:
                                    results.append({
                                        "source": "TinEye",
                                        "url": link['href'],
                                        "title": link.get_text(strip=True)[:100],
                                        "confidence": 0.8
                                    })
                except Exception as e:
                    print(f"Ошибка TinEye: {e}")

        except Exception as e:
            print(f"Ошибка при поиске в TinEye: {e}")

        return results

    async def search_social_media_by_face(self, image_path: str) -> List[Dict]:
        """
        Поиск в социальных сетях по лицу
        (Упрощенная версия - в реальности требует API ключей)

        Args:
            image_path: путь к изображению

        Returns:
            List найденных профилей
        """
        results = []

        # Извлекаем лица
        face_encodings = self.extract_faces(image_path)

        if len(face_encodings) == 0:
            return [{
                "error": "Лица не обнаружены на изображении",
                "confidence": 0.0
            }]

        # Здесь можно добавить интеграцию с API социальных сетей
        # Например, поиск похожих лиц через VK API, FindClone и т.д.

        results.append({
            "type": "face_detection",
            "faces_found": len(face_encodings),
            "note": "Обнаружено лиц на изображении",
            "confidence": 1.0
        })

        return results


async def search_by_image(image_path: str) -> Dict:
    """
    Основная функция поиска по изображению

    Args:
        image_path: путь к изображению

    Returns:
        Dict с результатами поиска
    """
    searcher = ReverseImageSearch()

    # Проверка существования файла
    if not os.path.exists(image_path):
        return {
            "error": "Файл не найден",
            "results": []
        }

    # Извлечение лиц
    face_encodings = searcher.extract_faces(image_path)

    # Параллельный поиск по всем сервисам
    google_task = searcher.search_google_images(image_path)
    yandex_task = searcher.search_yandex_images(image_path)
    tineye_task = searcher.search_tineye(image_path)
    social_task = searcher.search_social_media_by_face(image_path)

    # Ждем результаты
    google_results, yandex_results, tineye_results, social_results = await asyncio.gather(
        google_task,
        yandex_task,
        tineye_task,
        social_task,
        return_exceptions=True
    )

    # Обработка результатов
    all_results = []

    if isinstance(google_results, list):
        all_results.extend(google_results)
    if isinstance(yandex_results, list):
        all_results.extend(yandex_results)
    if isinstance(tineye_results, list):
        all_results.extend(tineye_results)
    if isinstance(social_results, list):
        all_results.extend(social_results)

    return {
        "image_path": image_path,
        "faces_detected": len(face_encodings),
        "results": all_results,
        "total_found": len(all_results)
    }
