# config.py – конфигурация
import os
from dotenv import load_dotenv
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN", "8134199009:AAHBaUXopxz-yWxY0MxC8DQyWKLrn5Y8SOY")  # Токен бота Telegram
DB_DSN = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/postgres")  # Строка подключения к БД
