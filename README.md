# Auth API с OAuth2 и JWT

API для аутентификации и авторизации пользователей с использованием OAuth2 и JWT токенов.

## Функциональность

- Регистрация и авторизация пользователей
- JWT токены для аутентификации
- Обновление токенов
- Разграничение прав доступа (пользователь/администратор)
- Управление пользователями (CRUD)
- Изменение пароля

## Технический стек

- Python 3.10+
- FastAPI 0.95+
- MongoDB (через Motor для асинхронной работы)
- Pydantic 2.0+
- JWT для токенов авторизации
- Passlib + Bcrypt для хеширования паролей

## Установка и запуск

1. Клонировать репозиторий
2. Создать виртуальное окружение:
   ```
   python -m venv venv
   source venv/bin/activate  # для Linux/macOS
   venv\Scripts\activate     # для Windows
   ```
3. Установить зависимости:
   ```
   pip install -r requirements.txt
   ```
4. Создать файл `.env` на основе `.env.example`
5. Запустить MongoDB
6. Запустить приложение:
   ```
   python main.py
   ```

После запуска API будет доступно по адресу http://localhost:8000

## API Endpoints

### Аутентификация

- `POST /api/auth/register` - Регистрация нового пользователя
- `POST /api/auth/login` - Авторизация и получение JWT токена
- `POST /api/auth/refresh-token` - Обновление JWT токена
- `POST /api/auth/change-password` - Изменение пароля

### Пользователи

- `GET /api/users/me` - Получение информации о текущем пользователе
- `PUT /api/users/me` - Обновление информации о текущем пользователе
- `GET /api/users` - Получение списка пользователей (только для администраторов)
- `GET /api/users/{user_id}` - Получение информации о пользователе
- `PUT /api/users/{user_id}` - Обновление информации о пользователе (только для администраторов)
- `DELETE /api/users/{user_id}` - Удаление пользователя (только для администраторов)

## Примеры запросов

### Регистрация пользователя

```
POST /api/auth/register
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securepassword",
  "full_name": "John Doe"
}
```

### Авторизация и получение токена

```
POST /api/auth/login
{
  "username": "john_doe",
  "password": "securepassword"
}
```

### Использование JWT токена

Для защищенных эндпоинтов необходимо добавить заголовок авторизации:

```
Authorization: Bearer your_jwt_token_here
```

## Роли пользователей

- **USER** - обычный пользователь с базовыми правами
- **ADMIN** - администратор с полными правами управления
