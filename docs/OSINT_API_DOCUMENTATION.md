# PeopleFinder OSINT API v2.0 - Документация

## Обзор

**PeopleFinder OSINT API** - профессиональный инструмент для OSINT исследований с интеграцией реальных open-source библиотек.

## Базовый URL

```
http://localhost:8000
```

## Аутентификация

В текущей версии аутентификация не требуется (dev mode).

---

## 🔥 Новые OSINT Endpoints

### 1. Email OSINT Check

**Endpoint:** `POST /api/osint/email`

**Описание:** Глубокая проверка email адреса через множество источников

**Интеграции:**
- HaveIBeenPwned - проверка утечек паролей
- Holehe logic - проверка регистраций на популярных сайтах
- DNS/MX validation - проверка валидности email

**Request Body:**
```json
{
  "email": "user@example.com",
  "check_breaches": true,
  "check_registrations": true
}
```

**Response:**
```json
{
  "success": true,
  "email": "user@example.com",
  "data": {
    "metadata": {
      "username": "user",
      "domain": "example.com",
      "provider": "Unknown/Custom",
      "disposable": false,
      "mx_valid": true
    },
    "breaches": {
      "found": true,
      "breach_count": 3,
      "breaches": [
        {
          "name": "LinkedIn",
          "title": "LinkedIn",
          "domain": "linkedin.com",
          "breach_date": "2021-06-22",
          "data_classes": ["Email addresses", "Passwords"],
          "pwn_count": 700000000
        }
      ]
    },
    "registrations": {
      "email": "user@example.com",
      "registrations_found": 4,
      "sites": [
        {
          "site": "GitHub",
          "registered": "yes",
          "confidence": 0.9
        },
        {
          "site": "Instagram",
          "registered": "likely",
          "confidence": 0.7
        }
      ]
    },
    "summary": {
      "total_breaches": 3,
      "total_registrations": 4,
      "risk_level": "high"
    }
  },
  "processing_time": 2.34,
  "timestamp": 1706727600
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/osint/email \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@gmail.com",
    "check_breaches": true,
    "check_registrations": true
  }'
```

---

### 2. Username OSINT Check

**Endpoint:** `POST /api/osint/username`

**Описание:** Глубокий поиск username на 20+ платформах с извлечением метаданных

**Интеграции:**
- Maigret logic - расширенная база сайтов (500+)
- socid-extractor logic - извлечение профильных данных
- Категоризация по типам платформ

**Request Body:**
```json
{
  "username": "johndoe",
  "max_sites": 20,
  "extract_metadata": true
}
```

**Response:**
```json
{
  "success": true,
  "username": "johndoe",
  "data": {
    "total_found": 8,
    "results": [
      {
        "platform": "GitHub",
        "url": "https://github.com/johndoe",
        "status": "found",
        "confidence": 0.95,
        "http_status": 200,
        "tags": ["coding", "tech"],
        "full_name": "John Doe",
        "avatar_url": "https://avatars.githubusercontent.com/u/12345",
        "bio": "Software Engineer"
      },
      {
        "platform": "Instagram",
        "url": "https://www.instagram.com/johndoe",
        "status": "found",
        "confidence": 0.95,
        "tags": ["social", "photo"]
      }
    ],
    "by_category": {
      "social": ["Instagram", "Twitter", "VK"],
      "tech": ["GitHub", "Habr"],
      "professional": ["LinkedIn"]
    },
    "summary": {
      "platforms_found": 8,
      "with_full_name": 4,
      "with_avatar": 5,
      "with_bio": 3,
      "high_confidence": 7
    }
  },
  "processing_time": 3.56,
  "timestamp": 1706727600
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/osint/username \
  -H "Content-Type: application/json" \
  -d '{
    "username": "github",
    "max_sites": 20,
    "extract_metadata": true
  }'
```

---

### 3. Photo OSINT Search

**Endpoint:** `POST /api/osint/photo`

**Описание:** Reverse image search через Yandex, Google и TinEye

**Интеграции:**
- Yandex Images - лучший для российских профилей и VK
- Google Images - глобальный поиск
- TinEye - специализированный reverse search
- Автоматическое извлечение социальных профилей

**Request:**
```
Content-Type: multipart/form-data
file: <binary image data>
```

**Response:**
```json
{
  "success": true,
  "filename": "photo.jpg",
  "data": {
    "image_path": "/path/to/photo.jpg",
    "total_results": 25,
    "results": {
      "yandex": [
        {
          "source": "Yandex Images",
          "thumbnail": "https://...",
          "url": "https://vk.com/id12345",
          "similarity": 0.8,
          "index": 0
        }
      ],
      "google": [...],
      "tineye": [...]
    },
    "social_profiles": [
      {
        "network": "VKontakte",
        "url": "https://vk.com/id12345",
        "domain": "vk.com",
        "similarity": 0.8,
        "source": "Yandex Images"
      },
      {
        "network": "Instagram",
        "url": "https://instagram.com/user123",
        "domain": "instagram.com",
        "similarity": 0.75,
        "source": "Google Images"
      }
    ],
    "summary": {
      "total_found": 25,
      "social_profiles_found": 5,
      "unique_domains": 12
    }
  },
  "processing_time": 8.92,
  "timestamp": 1706727600
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/osint/photo \
  -F "file=@/path/to/photo.jpg"
```

---

## 📊 Batch Operations

### Batch Username Check

**Endpoint:** `POST /api/osint/batch/usernames`

**Описание:** Пакетная проверка до 20 usernames

**Request Body:**
```json
{
  "usernames": ["user1", "user2", "user3"],
  "max_sites": 10
}
```

**Response:**
```json
{
  "success": true,
  "total_checked": 3,
  "results": [
    {
      "username": "user1",
      "success": true,
      "data": {...}
    },
    {
      "username": "user2",
      "success": true,
      "data": {...}
    }
  ]
}
```

---

## 🔧 Utility Endpoints

### Health Check

**Endpoint:** `GET /api/health`

**Response:**
```json
{
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
```

### API Info

**Endpoint:** `GET /api/info`

Полная информация об API и доступных методах

### Cleanup

**Endpoint:** `DELETE /api/cleanup`

Очистка загруженных файлов

---

## 🚀 Quick Start

### Python Example

```python
import requests

# Email Check
email_check = requests.post(
    "http://localhost:8000/api/osint/email",
    json={
        "email": "test@gmail.com",
        "check_breaches": True,
        "check_registrations": True
    }
)
print(email_check.json())

# Username Check
username_check = requests.post(
    "http://localhost:8000/api/osint/username",
    json={
        "username": "github",
        "max_sites": 20,
        "extract_metadata": True
    }
)
print(username_check.json())

# Photo Check
with open("photo.jpg", "rb") as f:
    photo_check = requests.post(
        "http://localhost:8000/api/osint/photo",
        files={"file": f}
    )
print(photo_check.json())
```

### JavaScript Example

```javascript
// Email Check
const emailCheck = await fetch('http://localhost:8000/api/osint/email', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    email: 'test@gmail.com',
    check_breaches: true,
    check_registrations: true
  })
});
const emailResult = await emailCheck.json();

// Username Check
const usernameCheck = await fetch('http://localhost:8000/api/osint/username', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    username: 'github',
    max_sites: 20,
    extract_metadata: true
  })
});
const usernameResult = await usernameCheck.json();

// Photo Check
const formData = new FormData();
formData.append('file', photoFile);
const photoCheck = await fetch('http://localhost:8000/api/osint/photo', {
  method: 'POST',
  body: formData
});
const photoResult = await photoCheck.json();
```

---

## 📝 Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request (invalid input) |
| 404 | Not Found |
| 500 | Internal Server Error |

---

## ⚠️ Rate Limiting

Рекомендуется:
- Email checks: макс. 10 запросов/минуту
- Username checks: макс. 5 запросов/минуту
- Photo searches: макс. 3 запроса/минуту

---

## 🔐 Безопасность и Этика

**ВАЖНО:**
1. Используйте только для легальных OSINT исследований
2. Соблюдайте законы о защите данных (GDPR, CCPA)
3. Не используйте для харассмента или преследования
4. Уважайте приватность людей
5. Данные утечек используйте только для оповещения пострадавших

---

## 📚 Интегрированные OSINT Tools

1. **HaveIBeenPwned** - Проверка утечек паролей (800+ млн аккаунтов)
2. **Holehe** - Логика проверки регистраций email (100+ сайтов)
3. **Maigret** - Логика глубокого поиска username (500+ сайтов)
4. **Yandex Images** - Лучший reverse search для РФ
5. **Google Images** - Глобальный reverse search
6. **TinEye** - Специализированный reverse search

---

## 🐛 Troubleshooting

### Email проверка не работает
- Проверьте доступность HIBP API
- Убедитесь что email валидный

### Username поиск медленный
- Уменьшите `max_sites`
- Используйте batch операции

### Photo search возвращает мало результатов
- Качество изображения может влиять на результаты
- Yandex лучше работает с лицами из РФ
- Google лучше для глобального поиска

---

## 📖 Дополнительная документация

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

**Version:** 2.0.0
**Last Updated:** 2024-01-31
