import aiosqlite
import os
from pathlib import Path

class Database:
    def __init__(self, db_path: str = "bot.db"):
        self.db_path = db_path
        self.conn: aiosqlite.Connection | None = None

    async def connect(self):
        """Установить соединение с SQLite и создать таблицы, если нужно."""
        # Ensure the database file is created in the project directory
        base_dir = Path(__file__).parent
        db_file = base_dir / self.db_path
        db_file.parent.mkdir(parents=True, exist_ok=True)

        self.conn = await aiosqlite.connect(db_file.as_posix())
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                username TEXT
            );
        """)
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS builds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                cpu_id INTEGER,
                motherboard_id INTEGER,
                ram_id INTEGER,
                gpu_id INTEGER,
                storage_id INTEGER,
                case_id INTEGER,
                psu_id INTEGER,
                cooler_id INTEGER,
                total_price INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await self.conn.commit()
        print("SQLite connected and tables ensured")

    async def add_user(self, telegram_id: int, username: str):
        """Добавить пользователя в БД (если не существует)."""
        await self.conn.execute(
            "INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)",
            (telegram_id, username)
        )
        await self.conn.commit()

    async def log_action(self, user_id: int, action: str):
        """Логирование действия пользователя."""
        await self.conn.execute(
            "INSERT INTO logs (user_id, action) VALUES (?, ?)",
            (user_id, action)
        )
        await self.conn.commit()

    async def get_user_id(self, telegram_id: int):
        """Получить внутренний id пользователя по Telegram ID."""
        cursor = await self.conn.execute(
            "SELECT id FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None

    # --- Ниже добавлены методы-заглушки ---

    async def select_cpus(self, usage: str = None, max_price: int = None):
        """Возвращает тестовый список CPU."""
        return [
            {'id': 1, 'name': 'Intel Core i5-10400F', 'price': 12000, 'socket': 'LGA1200', 'tdp': 65},
            {'id': 2, 'name': 'Intel Core i3-10100',  'price': 8000,  'socket': 'LGA1200', 'tdp': 65},
            {'id': 3, 'name': 'AMD Ryzen 5 3600',    'price': 14000, 'socket': 'AM4',      'tdp': 65},
            {'id': 4, 'name': 'AMD Ryzen 7 3700X',   'price': 22000, 'socket': 'AM4',      'tdp': 95},
        ]

    async def select_motherboards(self, socket: str = None, max_price: int = None):
        """Возвращает тестовый список материнских плат."""
        options = [
            {'id': 1, 'name': 'MSI B460M PRO', 'price': 7000, 'socket': 'LGA1200', 'ram_type': 'DDR4', 'form_factor': 'mATX'},
            {'id': 2, 'name': 'ASUS PRIME H410M', 'price': 5000, 'socket': 'LGA1200', 'ram_type': 'DDR4', 'form_factor': 'mATX'},
        ]
        if socket:
            return [m for m in options if m['socket'] == socket]
        return options

    async def select_rams(self, ram_type: str = None, needed_size: int = None, max_price: int = None):
        """Возвращает тестовый список RAM."""
        return [
            {'id': 1, 'name': '8GB DDR4-2400',  'price': 2000, 'type': 'DDR4'},
            {'id': 2, 'name': '8GB DDR4-3200',  'price': 2200, 'type': 'DDR4'},
            {'id': 3, 'name': '16GB DDR4-3200', 'price': 4000, 'type': 'DDR4'},
            {'id': 4, 'name': '32GB DDR4-3600', 'price': 8000, 'type': 'DDR4'},
        ]

    async def select_gpus(self, max_price: int = None):
        """Возвращает тестовый список GPU."""
        return [
            {'id': 1, 'name': 'NVIDIA GTX 1050 Ti',    'price': 9000,  'tdp': 75},
            {'id': 2, 'name': 'NVIDIA GTX 1660 Super', 'price': 20000, 'tdp': 125},
            {'id': 3, 'name': 'NVIDIA RTX 2060',       'price': 30000, 'tdp': 160},
        ]

    async def select_storages(self, min_capacity: int = None, max_price: int = None):
        """Возвращает тестовый список накопителей."""
        return [
            {'id': 1, 'name': '256GB SSD',     'price': 3000,  'capacity': 256},
            {'id': 2, 'name': '512GB SSD',     'price': 6000,  'capacity': 512},
            {'id': 3, 'name': '1TB NVMe SSD',  'price': 10000, 'capacity': 1024},
        ]

    async def select_cases(self, form_factor: str = None, gpu_length: int = None, max_price: int = None):
        """Возвращает тестовый список корпусов."""
        return [
            {'id': 1, 'name': 'Budget Case',         'price': 1500, 'form_factor': 'mATX',    'gpu_max_length': 300},
            {'id': 2, 'name': 'Mid Tower Case',      'price': 2500, 'form_factor': 'ATX',     'gpu_max_length': 350},
            {'id': 3, 'name': 'Mini ITX Case',       'price': 2000, 'form_factor': 'Mini-ITX','gpu_max_length': 280},
        ]

    async def select_psus(self, required_power: int = None, max_price: int = None):
        """Возвращает тестовый список блоков питания."""
        return [
            {'id': 1, 'name': '450W PSU',          'price': 2000, 'power': 450},
            {'id': 2, 'name': '550W Bronze PSU',   'price': 3500, 'power': 550},
            {'id': 3, 'name': '650W Gold PSU',     'price': 5000, 'power': 650},
        ]

    async def select_coolers(self, socket: str = None, required_tdp: int = None, max_price: int = None):
        """Возвращает тестовый список кулеров."""
        return [
            {'id': 1, 'name': 'Stock Cooler',               'price': 800,  'socket': socket, 'tdp_capacity': 65},
            {'id': 2, 'name': 'Aftermarket Air Cooler',     'price': 3000, 'socket': socket, 'tdp_capacity': 150},
            {'id': 3, 'name': 'Liquid Cooler 240mm',        'price': 6000, 'socket': socket, 'tdp_capacity': 200},
        ]

    async def save_build(self, user_id: int, build: dict):
        """Сохранить сборку в БД."""
        await self.conn.execute(
            """
            INSERT INTO builds
            (user_id, cpu_id, motherboard_id, ram_id, gpu_id,
             storage_id, case_id, psu_id, cooler_id, total_price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                build.get('cpu_id'),
                build.get('motherboard_id'),
                build.get('ram_id'),
                build.get('gpu_id'),
                build.get('storage_id'),
                build.get('case_id'),
                build.get('psu_id'),
                build.get('cooler_id'),
                build.get('total_price'),
            )
        )
        await self.conn.commit()

    async def get_builds(self, user_id: int):
        """Получить все сохранённые сборки пользователя."""
        cursor = await self.conn.execute(
            "SELECT * FROM builds WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        rows = await cursor.fetchall()
        cols = [desc[0] for desc in cursor.description]
        result = []
        for row in rows:
            rec = dict(zip(cols, row))
            result.append(rec)
        return result