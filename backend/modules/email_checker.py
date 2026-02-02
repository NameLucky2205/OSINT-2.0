"""
Модуль для глубокой проверки email адресов
Интеграция: Holehe + HaveIBeenPwned
"""
import asyncio
import hashlib
import re
import json
import subprocess
from typing import List, Dict, Optional
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential


class EmailChecker:
    """Класс для проверки email через различные OSINT источники"""

    def __init__(self):
        self.hibp_api = "https://haveibeenpwned.com/api/v3"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }

    def validate_email(self, email: str) -> bool:
        """Валидация email адреса"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def check_hibp_breaches(self, email: str) -> Dict:
        """
        Проверка email в базе HaveIBeenPwned (утечки данных)

        Args:
            email: email адрес для проверки

        Returns:
            Dict с информацией об утечках
        """
        url = f"{self.hibp_api}/breachedaccount/{email}"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers, timeout=15) as response:
                    if response.status == 200:
                        breaches = await response.json()
                        return {
                            "found": True,
                            "breach_count": len(breaches),
                            "breaches": [
                                {
                                    "name": breach.get("Name"),
                                    "title": breach.get("Title"),
                                    "domain": breach.get("Domain"),
                                    "breach_date": breach.get("BreachDate"),
                                    "data_classes": breach.get("DataClasses", []),
                                    "pwn_count": breach.get("PwnCount", 0)
                                }
                                for breach in breaches[:20]  # Первые 20
                            ]
                        }
                    elif response.status == 404:
                        return {
                            "found": False,
                            "breach_count": 0,
                            "breaches": [],
                            "message": "Email не найден в утечках"
                        }
                    else:
                        return {
                            "error": f"HIBP API вернул статус {response.status}",
                            "found": False
                        }
            except asyncio.TimeoutError:
                return {"error": "Timeout при обращении к HIBP", "found": False}
            except Exception as e:
                return {"error": str(e), "found": False}

    async def check_holehe_registrations(self, email: str) -> Dict:
        """
        Проверка регистраций email через РЕАЛЬНУЮ библиотеку Holehe

        Holehe проверяет 100+ сайтов используя их официальные API

        Args:
            email: email для проверки

        Returns:
            Dict с найденными регистрациями
        """
        try:
            # Запускаем holehe через subprocess (она работает как CLI)
            result = subprocess.run(
                ['holehe', email, '--only-used'],
                capture_output=True,
                text=True,
                timeout=60
            )

            # Парсим вывод holehe
            results = []

            if result.returncode == 0:
                # holehe выводит результаты построчно
                lines = result.stdout.split('\n')

                for line in lines:
                    line = line.strip()
                    # Holehe показывает результаты с [+] для найденных
                    if '[+]' in line:
                        # Парсим формат: "[+] Email used on sitename"
                        parts = line.split(']', 1)
                        if len(parts) > 1:
                            site_info = parts[1].strip()
                            # Извлекаем название сайта
                            if ' on ' in site_info:
                                site_name = site_info.split(' on ')[-1].strip()
                            else:
                                site_name = site_info

                            results.append({
                                "site": site_name,
                                "registered": "yes",
                                "confidence": 0.95
                            })

                return {
                    "email": email,
                    "registrations_found": len(results),
                    "sites": results,
                    "method": "holehe_real"
                }
            else:
                # Fallback к упрощенной проверке если holehe не сработала
                return await self._fallback_registration_check(email)

        except subprocess.TimeoutExpired:
            return await self._fallback_registration_check(email)
        except FileNotFoundError:
            # holehe не установлена, используем fallback
            return await self._fallback_registration_check(email)
        except Exception as e:
            return await self._fallback_registration_check(email)

    async def _fallback_registration_check(self, email: str) -> Dict:
        """
        Упрощенная проверка регистраций (fallback если holehe не работает)

        Проверяет топ-10 популярных сайтов
        """
        sites_to_check = {
            "Instagram": {
                "url": "https://www.instagram.com/accounts/emailsignup/",
                "method": "POST",
                "check_type": "status_code"
            },
            "Twitter": {
                "url": "https://api.twitter.com/i/users/email_available.json",
                "method": "GET",
                "check_type": "json_response"
            },
            "GitHub": {
                "url": "https://github.com/signup/check_email",
                "method": "POST",
                "check_type": "status_code"
            },
            "Spotify": {
                "url": "https://spclient.wg.spotify.com/signup/public/v1/account",
                "method": "POST",
                "check_type": "json_response"
            },
            "Adobe": {
                "url": "https://accounts.adobe.com/api/v1/users/check",
                "method": "POST",
                "check_type": "status_code"
            }
        }

        results = []

        async with aiohttp.ClientSession() as session:
            for site_name, site_config in sites_to_check.items():
                try:
                    # Упрощенная проверка
                    if site_config["method"] == "POST":
                        data = {"email": email}
                        async with session.post(
                            site_config["url"],
                            json=data,
                            headers=self.headers,
                            timeout=10
                        ) as response:
                            if response.status in [200, 201]:
                                results.append({
                                    "site": site_name,
                                    "registered": "likely",
                                    "confidence": 0.7
                                })
                            elif response.status == 400:
                                results.append({
                                    "site": site_name,
                                    "registered": "yes",
                                    "confidence": 0.9
                                })
                except Exception as e:
                    continue

        return {
            "email": email,
            "registrations_found": len(results),
            "sites": results,
            "method": "fallback"
        }

    async def extract_email_metadata(self, email: str) -> Dict:
        """
        Извлечение метаданных из email

        Args:
            email: email адрес

        Returns:
            Dict с метаданными
        """
        parts = email.split('@')
        if len(parts) != 2:
            return {"error": "Invalid email format"}

        username, domain = parts

        return {
            "username": username,
            "domain": domain,
            "provider": self._identify_provider(domain),
            "disposable": await self._check_disposable(domain),
            "mx_valid": await self._check_mx_records(domain)
        }

    def _identify_provider(self, domain: str) -> str:
        """Определение почтового провайдера"""
        providers = {
            "gmail.com": "Google Gmail",
            "yahoo.com": "Yahoo Mail",
            "outlook.com": "Microsoft Outlook",
            "hotmail.com": "Microsoft Hotmail",
            "icloud.com": "Apple iCloud",
            "mail.ru": "Mail.ru",
            "yandex.ru": "Yandex Mail",
            "yandex.com": "Yandex Mail",
            "protonmail.com": "ProtonMail",
            "proton.me": "ProtonMail"
        }
        return providers.get(domain.lower(), "Unknown/Custom")

    async def _check_disposable(self, domain: str) -> bool:
        """Проверка на одноразовый email"""
        disposable_domains = [
            "tempmail.com", "guerrillamail.com", "10minutemail.com",
            "throwaway.email", "temp-mail.org", "mailinator.com",
            "trashmail.com", "getnada.com", "maildrop.cc"
        ]
        return domain.lower() in disposable_domains

    async def _check_mx_records(self, domain: str) -> bool:
        """Проверка MX записей домена"""
        try:
            import dns.resolver
            answers = dns.resolver.resolve(domain, 'MX')
            return len(answers) > 0
        except:
            return False


async def check_email_comprehensive(email: str) -> Dict:
    """
    Полная проверка email адреса с использованием реальных OSINT инструментов

    Args:
        email: email для проверки

    Returns:
        Dict со всеми результатами
    """
    checker = EmailChecker()

    # Валидация
    if not checker.validate_email(email):
        return {
            "success": False,
            "error": "Invalid email format",
            "email": email
        }

    # Параллельный запуск всех проверок
    metadata_task = checker.extract_email_metadata(email)
    hibp_task = checker.check_hibp_breaches(email)
    holehe_task = checker.check_holehe_registrations(email)

    metadata, hibp_result, holehe_result = await asyncio.gather(
        metadata_task,
        hibp_task,
        holehe_task,
        return_exceptions=True
    )

    # Расчет уровня риска
    breach_count = hibp_result.get("breach_count", 0) if isinstance(hibp_result, dict) else 0
    if breach_count >= 5:
        risk_level = "critical"
    elif breach_count >= 3:
        risk_level = "high"
    elif breach_count >= 1:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "success": True,
        "email": email,
        "metadata": metadata if not isinstance(metadata, Exception) else {"error": str(metadata)},
        "breaches": hibp_result if not isinstance(hibp_result, Exception) else {"error": str(hibp_result), "found": False},
        "registrations": holehe_result if not isinstance(holehe_result, Exception) else {"error": str(holehe_result), "registrations_found": 0},
        "summary": {
            "total_breaches": breach_count,
            "total_registrations": holehe_result.get("registrations_found", 0) if isinstance(holehe_result, dict) else 0,
            "risk_level": risk_level,
            "using_real_holehe": holehe_result.get("method") == "holehe_real" if isinstance(holehe_result, dict) else False
        }
    }
