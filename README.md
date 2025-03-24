# URL Shortener Service

Сервис для создания коротких ссылок с использованием FastAPI, PostgreSQL и Redis.

## Возможности

- Создание коротких ссылок
- Группировка ссылок по проектам
- Статистика переходов
- Кэширование популярных ссылок
- Аутентификация пользователей
- API документация (Swagger UI)

## Требования

- Python 3.8+
- PostgreSQL
- Redis
- Poetry (для управления зависимостями)

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/url-shortener.git
cd url-shortener
```

2. Установите зависимости:
```bash
poetry install
```

3. Создайте файл .env:
```env
DATABASE_URL="postgresql+asyncpg://postgres:your_password@localhost:5432/url_shortener"
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=url_shortener

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

4. Примените миграции:
```bash
alembic upgrade head
```

## Запуск

```bash
uvicorn main:app --reload
```

## API Endpoints

### Аутентификация
- POST /api/auth/register - Регистрация пользователя
- POST /api/auth/login - Вход в систему

### Ссылки
- POST /api/links/shorten - Создание короткой ссылки
- GET /api/links/ - Список ссылок пользователя
- GET /api/links/{short_code}/stats - Статистика по ссылке
- GET /api/links/popular - Популярные ссылки
- GET /{short_code} - Редирект по короткой ссылке

### Проекты
- POST /api/projects/ - Создание проекта
- GET /api/projects/ - Список проектов пользователя
- PUT /api/projects/{project_id} - Обновление проекта
- DELETE /api/projects/{project_id} - Удаление проекта

## Документация API

После запуска сервера, документация доступна по адресу:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc 