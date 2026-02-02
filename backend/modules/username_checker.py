"""
Модуль для глубокого поиска по username
Интеграция: Maigret (реальная база 500+ сайтов) + socid-extractor
"""
import asyncio
import json
import subprocess
import tempfile
from typing import List, Dict, Optional
import aiohttp
from pathlib import Path


class UsernameChecker:
    """
    Класс для глубокого поиска username через Maigret
    Maigret - это улучшенная версия Sherlock с извлечением метаданных
    """

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        # База расширенных сайтов для fallback (если maigret не сработает)
        self.fallback_sites = self._load_fallback_sites()

    def _load_fallback_sites(self) -> Dict:
        """
        Загрузка базы данных сайтов для fallback
        Используется если maigret не работает
        """
        return {
            "GitHub": {
                "url": "https://github.com/{}",
                "urlMain": "https://github.com/",
                "errorType": "status_code",
                "tags": ["coding", "tech"]
            },
            "Instagram": {
                "url": "https://www.instagram.com/{}/",
                "urlMain": "https://www.instagram.com/",
                "errorType": "status_code",
                "tags": ["social", "photo"]
            },
            "Twitter": {
                "url": "https://twitter.com/{}",
                "urlMain": "https://twitter.com/",
                "errorType": "status_code",
                "tags": ["social", "news"]
            },
            "Reddit": {
                "url": "https://www.reddit.com/user/{}",
                "urlMain": "https://www.reddit.com/",
                "errorType": "status_code",
                "tags": ["social", "forum"]
            },
            "Medium": {
                "url": "https://medium.com/@{}",
                "urlMain": "https://medium.com/",
                "errorType": "status_code",
                "tags": ["blogging", "writing"]
            },
            "YouTube": {
                "url": "https://www.youtube.com/@{}",
                "urlMain": "https://www.youtube.com/",
                "errorType": "status_code",
                "tags": ["video", "social"]
            },
            "TikTok": {
                "url": "https://www.tiktok.com/@{}",
                "urlMain": "https://www.tiktok.com/",
                "errorType": "status_code",
                "tags": ["video", "social"]
            },
            "Telegram": {
                "url": "https://t.me/{}",
                "urlMain": "https://t.me/",
                "errorType": "status_code",
                "tags": ["messenger", "social"]
            },
            "VK": {
                "url": "https://vk.com/{}",
                "urlMain": "https://vk.com/",
                "errorType": "status_code",
                "tags": ["social", "russian"]
            },
            "Habr": {
                "url": "https://habr.com/ru/users/{}",
                "urlMain": "https://habr.com/",
                "errorType": "status_code",
                "tags": ["tech", "russian", "blogging"]
            },
            "Behance": {
                "url": "https://www.behance.net/{}",
                "urlMain": "https://www.behance.net/",
                "errorType": "status_code",
                "tags": ["design", "portfolio"]
            },
            "Dribbble": {
                "url": "https://dribbble.com/{}",
                "urlMain": "https://dribbble.com/",
                "errorType": "status_code",
                "tags": ["design", "portfolio"]
            },
            "LinkedIn": {
                "url": "https://www.linkedin.com/in/{}",
                "urlMain": "https://www.linkedin.com/",
                "errorType": "status_code",
                "tags": ["professional", "networking"]
            },
            "Twitch": {
                "url": "https://www.twitch.tv/{}",
                "urlMain": "https://www.twitch.tv/",
                "errorType": "status_code",
                "tags": ["gaming", "streaming"]
            },
            "Pinterest": {
                "url": "https://www.pinterest.com/{}",
                "urlMain": "https://www.pinterest.com/",
                "errorType": "status_code",
                "tags": ["photo", "social"]
            },
            "Tumblr": {
                "url": "https://{}.tumblr.com",
                "urlMain": "https://www.tumblr.com/",
                "errorType": "status_code",
                "tags": ["blogging", "social"]
            }
        }

    async def search_with_maigret(self, username: str, max_sites: int = None) -> Optional[Dict]:
        """
        Поиск username через РЕАЛЬНУЮ библиотеку Maigret

        Maigret имеет базу из 500+ сайтов и продвинутые методы проверки

        Args:
            username: username для поиска
            max_sites: максимальное количество сайтов (None = все)

        Returns:
            Dict с результатами или None если maigret не работает
        """
        try:
            # Создаем временный файл для вывода
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tf:
                output_file = tf.name

            # Формируем команду maigret
            cmd = ['maigret', username, '--json', 'simple', '--timeout', '10']

            # Если указано max_sites, используем топ сайты
            if max_sites:
                cmd.extend(['--top-sites', str(max_sites)])

            # Запускаем maigret
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2 минуты максимум
            )

            # Парсим вывод maigret
            if result.returncode == 0 or result.stdout:
                # Maigret выводит JSON в stdout или stderr
                output = result.stdout or result.stderr

                # Ищем JSON в выводе
                try:
                    # Maigret может выводить дополнительный текст, находим JSON
                    json_start = output.find('{')
                    json_end = output.rfind('}') + 1

                    if json_start >= 0 and json_end > json_start:
                        json_data = output[json_start:json_end]
                        maigret_results = json.loads(json_data)

                        # Конвертируем результаты maigret в наш формат
                        return await self._convert_maigret_results(username, maigret_results)
                except json.JSONDecodeError:
                    pass

            # Удаляем временный файл
            try:
                Path(output_file).unlink()
            except:
                pass

            return None

        except subprocess.TimeoutExpired:
            return None
        except FileNotFoundError:
            # maigret не установлен
            return None
        except Exception as e:
            return None

    async def _convert_maigret_results(self, username: str, maigret_data: Dict) -> Dict:
        """
        Конвертирует результаты maigret в наш формат

        Args:
            username: username
            maigret_data: данные от maigret

        Returns:
            Dict в нашем формате
        """
        results = []

        # Maigret возвращает словарь с найденными сайтами
        for site_name, site_data in maigret_data.items():
            if isinstance(site_data, dict) and site_data.get('status') == 'found':
                result = {
                    "platform": site_name,
                    "url": site_data.get('url', ''),
                    "status": "found",
                    "confidence": 0.95,
                    "http_status": site_data.get('http_status', 200),
                    "tags": site_data.get('tags', [])
                }

                # Добавляем метаданные если есть
                if 'name' in site_data:
                    result['full_name'] = site_data['name']
                if 'avatar_url' in site_data:
                    result['avatar_url'] = site_data['avatar_url']
                if 'bio' in site_data or 'description' in site_data:
                    result['bio'] = site_data.get('bio') or site_data.get('description')

                results.append(result)

        # Категоризация результатов
        categorized = self._categorize_results(results)

        return {
            "username": username,
            "total_found": len(results),
            "results": results,
            "by_category": categorized,
            "summary": self._generate_summary(results),
            "method": "maigret_real"
        }

    async def check_username_on_site(
        self,
        username: str,
        site_name: str,
        site_data: Dict,
        session: aiohttp.ClientSession
    ) -> Optional[Dict]:
        """
        Проверка username на конкретном сайте (fallback метод)

        Args:
            username: username для поиска
            site_name: название сайта
            site_data: данные о сайте
            session: aiohttp сессия

        Returns:
            Dict с результатами или None
        """
        url = site_data["url"].format(username)

        try:
            async with session.get(url, headers=self.headers, timeout=10, allow_redirects=True) as response:
                if response.status == 200:
                    # Пытаемся извлечь дополнительные данные
                    html = await response.text()
                    extracted_data = await self._extract_profile_data(html, site_name)

                    return {
                        "platform": site_name,
                        "url": url,
                        "status": "found",
                        "confidence": 0.95,
                        "http_status": response.status,
                        "tags": site_data.get("tags", []),
                        **extracted_data
                    }
                elif response.status == 404:
                    return None
                else:
                    return {
                        "platform": site_name,
                        "url": url,
                        "status": "uncertain",
                        "confidence": 0.5,
                        "http_status": response.status
                    }
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            return None

    async def _extract_profile_data(self, html: str, site_name: str) -> Dict:
        """
        Извлечение данных профиля из HTML (упрощенная версия socid-extractor)

        Args:
            html: HTML страницы
            site_name: название сайта

        Returns:
            Dict с извлеченными данными
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, 'html.parser')
        extracted = {}

        try:
            # Общая логика извлечения
            # Полное имя
            name_selectors = [
                ('meta', {'property': 'og:title'}),
                ('meta', {'name': 'twitter:title'}),
                ('h1', {}),
                ('span', {'class': 'ProfileHeaderCard-name'}),
            ]

            for tag, attrs in name_selectors:
                element = soup.find(tag, attrs)
                if element:
                    extracted['full_name'] = element.get('content') or element.get_text(strip=True)
                    break

            # Аватар
            avatar_selectors = [
                ('meta', {'property': 'og:image'}),
                ('img', {'class': 'avatar'}),
                ('img', {'class': 'profile-pic'}),
            ]

            for tag, attrs in avatar_selectors:
                element = soup.find(tag, attrs)
                if element:
                    extracted['avatar_url'] = element.get('content') or element.get('src')
                    break

            # Биография
            bio_selectors = [
                ('meta', {'property': 'og:description'}),
                ('meta', {'name': 'description'}),
                ('p', {'class': 'bio'}),
            ]

            for tag, attrs in bio_selectors:
                element = soup.find(tag, attrs)
                if element:
                    extracted['bio'] = element.get('content') or element.get_text(strip=True)
                    break

        except Exception as e:
            pass

        return extracted

    async def search_username_comprehensive(
        self,
        username: str,
        max_sites: Optional[int] = None
    ) -> Dict:
        """
        Полный поиск username по всем сайтам

        Сначала пытается использовать maigret (500+ сайтов),
        потом fallback на ручную проверку (16 сайтов)

        Args:
            username: username для поиска
            max_sites: максимальное количество сайтов

        Returns:
            Dict с результатами
        """
        if not username or len(username) < 2:
            return {"error": "Username слишком короткий", "results": []}

        # Сначала пытаемся использовать реальный maigret
        maigret_result = await self.search_with_maigret(username, max_sites)

        if maigret_result:
            return maigret_result

        # Fallback на ручную проверку
        sites_to_check = list(self.fallback_sites.items())
        if max_sites:
            sites_to_check = sites_to_check[:max_sites]

        results = []

        async with aiohttp.ClientSession() as session:
            tasks = [
                self.check_username_on_site(username, site_name, site_data, session)
                for site_name, site_data in sites_to_check
            ]

            results_raw = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results_raw:
                if result and isinstance(result, dict):
                    results.append(result)

        # Категоризация результатов
        categorized = self._categorize_results(results)

        return {
            "username": username,
            "total_found": len(results),
            "results": results,
            "by_category": categorized,
            "summary": self._generate_summary(results),
            "method": "fallback"
        }

    def _categorize_results(self, results: List[Dict]) -> Dict:
        """Категоризация результатов по типам платформ"""
        categories = {}

        for result in results:
            tags = result.get("tags", [])
            for tag in tags:
                if tag not in categories:
                    categories[tag] = []
                categories[tag].append(result["platform"])

        return categories

    def _generate_summary(self, results: List[Dict]) -> Dict:
        """Генерация сводки по результатам"""
        return {
            "platforms_found": len(results),
            "with_full_name": len([r for r in results if r.get("full_name")]),
            "with_avatar": len([r for r in results if r.get("avatar_url")]),
            "with_bio": len([r for r in results if r.get("bio")]),
            "high_confidence": len([r for r in results if r.get("confidence", 0) >= 0.8])
        }


async def check_username_full(username: str, max_sites: int = 20) -> Dict:
    """
    Главная функция для полного поиска по username

    Использует реальный Maigret если доступен (500+ сайтов),
    иначе fallback на ручную проверку (16 сайтов)

    Args:
        username: username для поиска
        max_sites: максимальное количество сайтов

    Returns:
        Dict с полными результатами
    """
    checker = UsernameChecker()
    return await checker.search_username_comprehensive(username, max_sites)
