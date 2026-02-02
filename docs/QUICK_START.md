# ⚡ Quick Start - PeopleFinder OSINT v2.1

## ⭐ Новое в v2.1

**Интеграция реальных OSINT инструментов:**
- ✅ **Holehe** - проверка email на 100+ сайтах (вместо 5)
- ✅ **Maigret** - поиск username на 500+ платформах (вместо 16)
- ✅ Fallback механизм для надежности
- ✅ Индикаторы использования реальных инструментов

---

## 1️⃣ Запуск сервера (если не запущен)

```bash
cd /Users/deus/dev/SP/SP/backend
source venv/bin/activate
python main_osint.py
```

Сервер запустится на `http://localhost:8000`

---

## 2️⃣ Доступные интерфейсы

### 🔥 OSINT Analytics Panel (Рекомендуется)
**URL:** http://localhost:8000/osint

**Возможности:**
- Профессиональная панель для аналитиков
- Email OSINT (утечки + регистрации)
- Username OSINT (20+ платформ)
- Photo OSINT (reverse search)
- Статистика в реальном времени
- JSON viewer
- Экспорт результатов

---

### 🎯 Simple UI
**URL:** http://localhost:8000/

**Возможности:**
- Минималистичный Google-style интерфейс
- Быстрый поиск
- Toggle между фото и данными

---

### 📚 API Documentation
**Swagger UI:** http://localhost:8000/docs
**ReDoc:** http://localhost:8000/redoc

---

## 3️⃣ Примеры использования

### Email OSINT (через cURL)
```bash
curl -X POST http://localhost:8000/api/osint/email \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@gmail.com",
    "check_breaches": true,
    "check_registrations": true
  }'
```

### Username OSINT (через cURL)
```bash
curl -X POST http://localhost:8000/api/osint/username \
  -H "Content-Type: application/json" \
  -d '{
    "username": "github",
    "max_sites": 20,
    "extract_metadata": true
  }'
```

### Photo OSINT (через cURL)
```bash
curl -X POST http://localhost:8000/api/osint/photo \
  -F "file=@/path/to/photo.jpg"
```

---

## 4️⃣ Что можно проверить?

### ✅ Email:
- Утечки данных (HaveIBeenPwned)
- Регистрации на сайтах (Holehe)
- Провайдер и MX записи
- Risk level оценка

### ✅ Username:
- GitHub, Instagram, Twitter, Reddit
- YouTube, TikTok, Telegram, VK
- LinkedIn, Medium, Habr
- Behance, Dribbble, Twitch
- Pinterest, Tumblr

### ✅ Photo:
- Yandex Images (лучший для РФ)
- Google Images
- TinEye
- Автоматическое извлечение соц. профилей

---

## 5️⃣ Быстрый тест

### Тест Email:
```bash
# Откройте панель
open http://localhost:8000/osint

# Введите любой email
# Нажмите "Investigate Email"
```

### Тест Username:
```bash
# Откройте панель
open http://localhost:8000/osint

# Tab: Username
# Введите: elonmusk
# Max Sites: 20
# Нажмите "Search Username"
```

---

## 6️⃣ Полезные ссылки

- **OSINT Panel Guide:** [OSINT_PANEL_GUIDE.md](OSINT_PANEL_GUIDE.md)
- **API Documentation:** [OSINT_API_DOCUMENTATION.md](OSINT_API_DOCUMENTATION.md)
- **Implementation Details:** [OSINT_IMPLEMENTATION_SUMMARY.md](OSINT_IMPLEMENTATION_SUMMARY.md)

---

## 🆘 Проблемы?

### Сервер не запускается:
```bash
# Проверить порт 8000
lsof -ti:8000 | xargs kill -9

# Запустить снова
python main_osint.py
```

### Модули не установлены:
```bash
cd /Users/deus/dev/SP/SP
pip install -r requirements.txt
```

---

**Готово! Начните с OSINT панели:** http://localhost:8000/osint 🔥
