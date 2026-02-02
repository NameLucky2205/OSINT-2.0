"""
Модуль поиска по username/email
Основан на логике проекта Sherlock
"""
import asyncio
import aiohttp
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import json

class SherlockSearch:
    """Класс для поиска username по различным социальным сетям"""

    def __init__(self):
        # База данных социальных сетей с паттернами проверки
        # Упрощенная версия из Sherlock
        self.sites_data = {
            "GitHub": {
                "url": "https://github.com/{}",
                "errorType": "status_code",
                "username_claimed": "blue",
                "username_unclaimed": "noexist"
            },
            "Instagram": {
                "url": "https://www.instagram.com/{}",
                "errorType": "status_code",
                "username_claimed": "instagram",
                "username_unclaimed": "noexist"
            },
            "Twitter": {
                "url": "https://twitter.com/{}",
                "errorType": "status_code",
                "username_claimed": "elonmusk",
                "username_unclaimed": "noexist"
            },
            "Reddit": {
                "url": "https://www.reddit.com/user/{}",
                "errorType": "status_code",
                "username_claimed": "blue",
                "username_unclaimed": "noexist"
            },
            "YouTube": {
                "url": "https://www.youtube.com/@{}",
                "errorType": "status_code",
                "username_claimed": "youtube",
                "username_unclaimed": "noexist"
            },
            "TikTok": {
                "url": "https://www.tiktok.com/@{}",
                "errorType": "status_code",
                "username_claimed": "tiktok",
                "username_unclaimed": "noexist"
            },
            "Facebook": {
                "url": "https://www.facebook.com/{}",
                "errorType": "status_code",
                "username_claimed": "facebook",
                "username_unclaimed": "noexist"
            },
            "LinkedIn": {
                "url": "https://www.linkedin.com/in/{}",
                "errorType": "status_code",
                "username_claimed": "linkedin",
                "username_unclaimed": "noexist"
            },
            "Telegram": {
                "url": "https://t.me/{}",
                "errorType": "status_code",
                "username_claimed": "telegram",
                "username_unclaimed": "noexist"
            },
            "VK": {
                "url": "https://vk.com/{}",
                "errorType": "status_code",
                "username_claimed": "vk",
                "username_unclaimed": "noexist"
            },
            "Medium": {
                "url": "https://medium.com/@{}",
                "errorType": "status_code",
                "username_claimed": "medium",
                "username_unclaimed": "noexist"
            },
            "Twitch": {
                "url": "https://www.twitch.tv/{}",
                "errorType": "status_code",
                "username_claimed": "twitch",
                "username_unclaimed": "noexist"
            },
            "Pinterest": {
                "url": "https://www.pinterest.com/{}",
                "errorType": "status_code",
                "username_claimed": "pinterest",
                "username_unclaimed": "noexist"
            },
            "Tumblr": {
                "url": "https://{}.tumblr.com",
                "errorType": "status_code",
                "username_claimed": "tumblr",
                "username_unclaimed": "noexist"
            },
            "Snapchat": {
                "url": "https://www.snapchat.com/add/{}",
                "errorType": "status_code",
                "username_claimed": "snapchat",
                "username_unclaimed": "noexist"
            }
        }

    async def check_username(self, username: str, site_name: str, site_data: Dict, session: aiohttp.ClientSession) -> Optional[Dict]:
        """
        Проверка существования username на конкретном сайте

        Args:
            username: имя пользователя для поиска
            site_name: название сайта
            site_data: данные о сайте (URL паттерн и т.д.)
            session: aiohttp сессия

        Returns:
            Dict с информацией о найденном профиле или None
        """
        url = site_data["url"].format(username)

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        try:
            async with session.get(url, headers=headers, timeout=10, allow_redirects=True) as response:
                # Проверка по статус-коду
                if response.status == 200:
                    return {
                        "platform": site_name,
                        "url": url,
                        "status": "found",
                        "confidence": 0.9  # Высокая уверенность при 200
                    }
                elif response.status == 404:
                    return None
                else:
                    # Неопределенный статус
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
            # Игнорируем ошибки подключения
            return None

    async def search_username(self, username: str, max_sites: Optional[int] = None) -> List[Dict]:
        """
        Поиск username по всем поддерживаемым сайтам

        Args:
            username: имя пользователя для поиска
            max_sites: максимальное количество сайтов для проверки

        Returns:
            List найденных профилей
        """
        if not username or len(username) < 3:
            return []

        # Валидация username (только буквы, цифры, _, -)
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return []

        results = []
        sites_to_check = list(self.sites_data.items())

        if max_sites:
            sites_to_check = sites_to_check[:max_sites]

        # Создаем асинхронную сессию
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Создаем задачи для параллельной проверки
            tasks = [
                self.check_username(username, site_name, site_data, session)
                for site_name, site_data in sites_to_check
            ]

            # Ждем завершения всех задач
            results_raw = await asyncio.gather(*tasks, return_exceptions=True)

            # Фильтруем результаты
            for result in results_raw:
                if result and isinstance(result, dict):
                    results.append(result)

        return results

    def search_email(self, email: str) -> List[Dict]:
        """
        Поиск по email (базовая реализация)
        Можно расширить через интеграцию с Have I Been Pwned API и т.д.

        Args:
            email: email для поиска

        Returns:
            List найденной информации
        """
        results = []

        # Валидация email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return []

        # Извлекаем username из email
        username = email.split('@')[0]
        domain = email.split('@')[1]

        results.append({
            "type": "email_info",
            "email": email,
            "username_part": username,
            "domain": domain,
            "confidence": 1.0,
            "note": "Извлечена информация из email адреса"
        })

        return results


async def search_by_text(query: str, search_type: str = "username", max_sites: int = 15) -> Dict:
    """
    Основная функция поиска по текстовым данным

    Args:
        query: строка поиска (username или email)
        search_type: тип поиска ('username' или 'email')
        max_sites: максимальное количество сайтов

    Returns:
        Dict с результатами поиска
    """
    searcher = SherlockSearch()

    if search_type == "email":
        results = searcher.search_email(query)
        return {
            "query": query,
            "type": "email",
            "results": results,
            "total_found": len(results)
        }
    else:
        results = await searcher.search_username(query, max_sites)
        return {
            "query": query,
            "type": "username",
            "results": results,
            "total_found": len(results)
        }
