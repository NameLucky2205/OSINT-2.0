# PeopleFinder - Быстрый старт

## Минимальная установка (5 минут)

### 1. Клонирование и настройка

```bash
# Перейдите в директорию с проектом
cd /Users/deus/dev/SP/SP

# Создайте виртуальное окружение
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# или
venv\Scripts\activate     # Windows

# Установите зависимости
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Настройка конфигурации

```bash
# Скопируйте пример конфигурации
cp .env.example .env

# Конфигурация по умолчанию уже готова к работе
```

### 3. Запуск сервера

```bash
cd backend
python main.py
```

Откройте браузер: **http://localhost:8000**

## Тестирование

### Поиск по Username

1. Выберите режим "Поиск по данным"
2. Введите тестовый username: `github`
3. Нажмите "Найти"

### Поиск по Фото

1. Выберите режим "Поиск по фото"
2. Загрузите любую фотографию с лицом
3. Нажмите "Найти по фото"

## API Примеры

### cURL - Поиск по username

```bash
curl -X POST http://localhost:8000/api/search/text \
  -H "Content-Type: application/json" \
  -d '{
    "query": "github",
    "search_type": "username",
    "max_sites": 15
  }'
```

### cURL - Поиск по изображению

```bash
curl -X POST http://localhost:8000/api/search/image \
  -F "file=@/path/to/photo.jpg"
```

## Troubleshooting

### Ошибка: "No module named 'face_recognition'"

```bash
# Установите зависимости системы
# macOS:
brew install cmake

# Ubuntu/Debian:
sudo apt-get install cmake python3-dev

# Затем переустановите
pip install dlib face-recognition
```

### Ошибка: "Port 8000 already in use"

```bash
# Измените порт в .env
PORT=8001

# Или убейте процесс на порту 8000
lsof -ti:8000 | xargs kill -9
```

## Документация API

Автоматическая документация доступна по адресам:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Следующие шаги

1. Прочитайте [PEOPLEFINDER_README.md](PEOPLEFINDER_README.md) для полной документации
2. Изучите код в `backend/modules/` для кастомизации
3. Настройте proxy в `.env` если необходимо

---

**Готово! Приложение запущено и готово к использованию.**
