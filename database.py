import os

import asyncpg
from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

pool: asyncpg.Pool | None = None


async def create_pool():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)


async def close_pool():
    if pool:
        await pool.close()


async def init_db():
    query = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT UNIQUE NOT NULL,
        first_name TEXT,
        username TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS patients (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE SET NULL,
    full_name TEXT NOT NULL,
    phone TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS operation_categories (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS operation_types (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES operation_categories(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (category_id, name)
);
CREATE TABLE IF NOT EXISTS operations (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    operation_type_id INTEGER NOT NULL REFERENCES operation_types(id) ON DELETE RESTRICT,
    operation_date DATE NOT NULL,
    arrival_time TIME,
    created_at TIMESTAMP DEFAULT NOW()
);
    """

    async with pool.acquire() as connection:
        await connection.execute(query)


async def create_patient(full_name: str, phone: str):
    query = """
    INSERT INTO patients (full_name, phone)
    VALUES ($1, $2)
    ON CONFLICT (phone)
    DO UPDATE SET
        full_name = EXCLUDED.full_name;
    """

    async with pool.acquire() as connection:
        await connection.execute(query, full_name, phone)


async def save_user(telegram_id: int, first_name: str | None, username: str | None):
    query = """
    INSERT INTO users (telegram_id, first_name, username)
    VALUES ($1, $2, $3)
    ON CONFLICT (telegram_id)
    DO UPDATE SET
        first_name = EXCLUDED.first_name,
        username = EXCLUDED.username;
    """

    async with pool.acquire() as connection:
        await connection.execute(query, telegram_id, first_name, username)


async def get_user_id_by_telegram_id(telegram_id: int) -> int | None:
    query = """
    SELECT id
    FROM users
    WHERE telegram_id = $1;
    """

    async with pool.acquire() as connection:
        return await connection.fetchval(query, telegram_id)


async def save_patient(telegram_id: int, full_name: str, phone: str):
    user_id = await get_user_id_by_telegram_id(telegram_id)

    if user_id is None:
        return

    query = """
    INSERT INTO patients (user_id, full_name, phone)
    VALUES ($1, $2, $3)
    ON CONFLICT (user_id)
    DO UPDATE SET
        full_name = EXCLUDED.full_name,
        phone = EXCLUDED.phone;
    """

    async with pool.acquire() as connection:
        await connection.execute(query, user_id, full_name, phone)


async def seed_operation_catalog():
    catalog = {
        "Маммопластика": [
            ("Увеличение груди", "Установка круглых и анатомических имплантов."),
            ("Подтяжка груди", "Устранение птоза с имплантами или без."),
            ("Уменьшение груди", "Уменьшение объема молочных желез."),
            ("Липофилинг груди", "Увеличение объема за счет пересадки собственного жира пациента."),
            ("Реконструктивные операции груди", "Коррекция тубулярной груди, замена имплантов, удаление грудных имплантов."),
            ("Гинекомастия", "Лечение и устранение гинекомастии."),
        ],
        "Пластика лица и шеи": [
            ("Блефаропластика", "Пластика верхних и нижних век, трансконъюнктивальная, круговая и ориентальная."),
            ("Ринопластика и септопластика", "Пластика кончика или спинки носа, исправление перегородки, открытая/закрытая и повторная ринопластика."),
            ("Омоложение лица", "SMAS-лифтинг, эндоскопическая подтяжка лба и бровей, чик-лифтинг, височный лифтинг."),
            ("Хейлопластика", "Операции Булхорн, Корнер-лифт, VY-пластика, удаление биополимерного геля из губ."),
            ("Отопластика", "Устранение лопоухости, коррекция формы ушных раковин и мочек."),
        ],
        "Контурная пластика тела и липомоделирование": [
            ("Абдоминопластика", "Пластика живота с переносом пупка, ушиванием диастаза и удалением кожно-жирового фартука."),
            ("Липосакция", "Классическая, водоструйная, ультразвуковая, VASER и FaceTite липосакция."),
            ("Липоскульптурирование / Липомоделирование", "Прорисовка спортивного рельефа тела, включая липофилинг ягодиц."),
            ("Формирование узкой талии", "Операция по методике Кудзаева без удаления ребер."),
            ("Брахиопластика и феморопластика", "Подтяжка кожи рук и внутренней поверхности бедер."),
            ("Глютеопластика", "Эндопротезирование ягодиц."),
        ],
        "Комплексные и интимные операции": [
            ("Симультанные операции", "Одномоментное выполнение нескольких вмешательств."),
            ("Интимная пластика", "Лабиопластика и другие виды женской эстетической хирургии."),
        ],
    }

    async with pool.acquire() as connection:
        for category_name, operation_types in catalog.items():
            category_id = await connection.fetchval(
                """
                INSERT INTO operation_categories (name)
                VALUES ($1)
                ON CONFLICT (name)
                DO UPDATE SET name = EXCLUDED.name
                RETURNING id;
                """,
                category_name,
            )

            for operation_name, description in operation_types:
                await connection.execute(
                    """
                    INSERT INTO operation_types (category_id, name, description)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (category_id, name)
                    DO UPDATE SET description = EXCLUDED.description;
                    """,
                    category_id,
                    operation_name,
                    description,
                )

async def find_patient_by_phone(phone: str):
    query = """
    SELECT id, full_name, phone
    FROM patients
    WHERE phone = $1;
    """

    async with pool.acquire() as connection:
        return await connection.fetchrow(query, phone)


async def get_operation_categories():
    query = """
    SELECT id, name
    FROM operation_categories
    ORDER BY id;
    """

    async with pool.acquire() as connection:
        return await connection.fetch(query)

async def get_operation_types_by_category(category_id: int):
    query = """
    SELECT id, name
    FROM operation_types
    WHERE category_id = $1
    ORDER BY id;
    """

    async with pool.acquire() as connection:
        return await connection.fetch(query, category_id)


async def create_operation(
    patient_id: int,
    operation_type_id: int,
    operation_date: str,
    arrival_time: str,
):
    query = """
    INSERT INTO operations (
        patient_id,
        operation_type_id,
        operation_date,
        arrival_time
    )
    VALUES ($1, $2, $3, $4);
    """

    async with pool.acquire() as connection:
        await connection.execute(
            query,
            patient_id,
            operation_type_id,
            operation_date,
            arrival_time,
        )