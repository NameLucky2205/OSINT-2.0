"""
Модуль для глубокого поиска по фотографии
Yandex Images Reverse Search + Google Images + TinEye
"""
import asyncio
import base64
import hashlib
from typing import List, Dict, Optional
from pathlib import Path
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urlencode, quote
import cloudscraper
from fake_useragent import UserAgent


class PhotoSearcher:
    """Класс для reverse image search через Yandex, Google и TinEye"""

    def __init__(self):
        self.ua = UserAgent()
        # CloudScraper для обхода Cloudflare
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )

    async def search_yandex_images(self, image_path: str) -> List[Dict]:
        """
        Reverse image search через Yandex Images

        Yandex лучше всего работает с российскими лицами и VK профилями

        Args:
            image_path: путь к изображению

        Returns:
            List найденных результатов
        """
        results = []

        try:
            # Шаг 1: Загрузка изображения на Yandex
            upload_url = "https://yandex.ru/images/touch/search"

            with open(image_path, 'rb') as f:
                image_data = f.read()

            # Формируем multipart данные
            files = {
                'upfile': ('image.jpg', image_data, 'image/jpeg')
            }

            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'Referer': 'https://yandex.ru/images/'
            }

            # Загружаем изображение
            response = self.scraper.post(
                upload_url,
                files=files,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                # Парсим результаты
                soup = BeautifulSoup(response.text, 'html.parser')

                # Ищем похожие изображения
                similar_images = soup.find_all('div', class_='cbir-similar__thumb')

                for idx, img_div in enumerate(similar_images[:15]):  # Первые 15
                    img_tag = img_div.find('img')
                    link_tag = img_div.find_parent('a')

                    if img_tag and link_tag:
                        result = {
                            "source": "Yandex Images",
                            "thumbnail": img_tag.get('src'),
                            "url": link_tag.get('href'),
                            "similarity": 0.8 - (idx * 0.02),  # Примерная оценка
                            "index": idx
                        }
                        results.append(result)

                # Ищем страницы где встречается изображение
                pages = soup.find_all('div', class_='cbir-sites__thumb')

                for page in pages[:10]:
                    link = page.find('a')
                    if link:
                        domain = self._extract_domain(link.get('href', ''))
                        results.append({
                            "source": "Yandex Images - Sites",
                            "url": link.get('href'),
                            "domain": domain,
                            "type": "webpage",
                            "similarity": 0.7
                        })

        except Exception as e:
            print(f"Ошибка Yandex search: {e}")

        return results

    async def search_google_images(self, image_path: str) -> List[Dict]:
        """
        Reverse image search через Google Images

        Args:
            image_path: путь к изображению

        Returns:
            List найденных результатов
        """
        results = []

        try:
            # Google Images Search by URL
            # Используем метод через Google Lens API
            upload_url = "https://lens.google.com/v3/upload"

            with open(image_path, 'rb') as f:
                image_data = f.read()

            # Кодируем в base64
            encoded_image = base64.b64encode(image_data).decode('utf-8')

            headers = {
                'User-Agent': self.ua.random,
                'Content-Type': 'application/x-www-form-urlencoded',
            }

            # Альтернативный метод - через обычный search
            search_url = "https://www.google.com/searchbyimage/upload"

            files = {
                'encoded_image': ('image.jpg', image_data, 'image/jpeg')
            }

            response = self.scraper.post(
                search_url,
                files=files,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Парсим результаты
                search_results = soup.find_all('div', class_='g')

                for idx, result in enumerate(search_results[:10]):
                    link_tag = result.find('a')
                    title_tag = result.find('h3')

                    if link_tag and title_tag:
                        results.append({
                            "source": "Google Images",
                            "url": link_tag.get('href'),
                            "title": title_tag.get_text(strip=True),
                            "similarity": 0.75 - (idx * 0.03),
                            "index": idx
                        })

        except Exception as e:
            print(f"Ошибка Google search: {e}")

        return results

    async def search_tineye(self, image_path: str) -> List[Dict]:
        """
        Reverse image search через TinEye

        Args:
            image_path: путь к изображению

        Returns:
            List найденных результатов
        """
        results = []

        try:
            upload_url = "https://tineye.com/search"

            with open(image_path, 'rb') as f:
                image_data = f.read()

            files = {
                'image': ('image.jpg', image_data, 'image/jpeg')
            }

            headers = {
                'User-Agent': self.ua.random,
            }

            response = self.scraper.post(
                upload_url,
                files=files,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                matches = soup.find_all('div', class_='match')

                for idx, match in enumerate(matches[:10]):
                    link = match.find('a', class_='image-link')
                    domain_tag = match.find('p', class_='domain')

                    if link:
                        results.append({
                            "source": "TinEye",
                            "url": link.get('href'),
                            "domain": domain_tag.get_text(strip=True) if domain_tag else "Unknown",
                            "similarity": 0.85,
                            "index": idx
                        })

        except Exception as e:
            print(f"Ошибка TinEye search: {e}")

        return results

    def _extract_domain(self, url: str) -> str:
        """Извлечение домена из URL"""
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return "unknown"

    async def extract_social_profiles(self, results: List[Dict]) -> List[Dict]:
        """
        Извлечение социальных профилей из результатов

        Ищет ссылки на VK, Instagram, Facebook и т.д.

        Args:
            results: результаты поиска

        Returns:
            List социальных профилей
        """
        social_networks = {
            'vk.com': 'VKontakte',
            'instagram.com': 'Instagram',
            'facebook.com': 'Facebook',
            'twitter.com': 'Twitter',
            'linkedin.com': 'LinkedIn',
            'ok.ru': 'Odnoklassniki',
            'youtube.com': 'YouTube'
        }

        profiles = []

        for result in results:
            url = result.get('url', '')
            domain = result.get('domain', self._extract_domain(url))

            for social_domain, network_name in social_networks.items():
                if social_domain in domain:
                    profiles.append({
                        "network": network_name,
                        "url": url,
                        "domain": domain,
                        "similarity": result.get('similarity', 0.5),
                        "source": result.get('source')
                    })
                    break

        return profiles


async def search_by_photo_advanced(image_path: str) -> Dict:
    """
    Полный поиск по фотографии через все сервисы

    Args:
        image_path: путь к изображению

    Returns:
        Dict с результатами от всех сервисов
    """
    searcher = PhotoSearcher()

    # Параллельный поиск
    yandex_task = searcher.search_yandex_images(image_path)
    google_task = searcher.search_google_images(image_path)
    tineye_task = searcher.search_tineye(image_path)

    yandex_results, google_results, tineye_results = await asyncio.gather(
        yandex_task,
        google_task,
        tineye_task,
        return_exceptions=True
    )

    # Обработка результатов
    all_results = []

    if isinstance(yandex_results, list):
        all_results.extend(yandex_results)
    if isinstance(google_results, list):
        all_results.extend(google_results)
    if isinstance(tineye_results, list):
        all_results.extend(tineye_results)

    # Извлечение социальных профилей
    social_profiles = await searcher.extract_social_profiles(all_results)

    return {
        "success": True,
        "image_path": image_path,
        "total_results": len(all_results),
        "results": {
            "yandex": yandex_results if isinstance(yandex_results, list) else [],
            "google": google_results if isinstance(google_results, list) else [],
            "tineye": tineye_results if isinstance(tineye_results, list) else [],
        },
        "all_results": all_results,
        "social_profiles": social_profiles,
        "summary": {
            "total_found": len(all_results),
            "social_profiles_found": len(social_profiles),
            "unique_domains": len(set([r.get('domain', '') for r in all_results if r.get('domain')]))
        }
    }
