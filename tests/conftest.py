import asyncio
from datetime import datetime
from uuid import uuid4
import pytest
from contextlib import ExitStack
from sqlalchemy import text
import pytest_asyncio
from src import init_app, settings
from src.security import get_password_hash
from src.db import get_db, session_manager
from src.redis import RedisClient
from httpx import AsyncClient
from pytest_postgresql import factories
from pytest_postgresql.janitor import DatabaseJanitor
from src.enums import RoleEnum


user_data = {"username": "username", "password": "password"}
admin_data = {"username": "super_user", "password": settings.SUPER_USER_PASSWORD}
default_avatar_data = {"name": "default_avatar", "size": 1, "location": "path"}


@pytest.fixture(autouse=True)
def app():
    with ExitStack():
        yield init_app(init_db=False)


@pytest_asyncio.fixture
async def client(app):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


test_db = factories.postgresql_proc(dbname="test_db", port=None)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def connection_test(test_db, event_loop):
    pg_host = test_db.host
    pg_port = test_db.port
    pg_user = test_db.user
    pg_db = test_db.dbname
    pg_password = test_db.password

    with DatabaseJanitor(
        pg_user, pg_host, pg_port, pg_db, test_db.version, pg_password
    ):
        test_db_url = f"postgresql+asyncpg://{pg_user}:@{pg_host}:{pg_port}/{pg_db}"
        session_manager.init(test_db_url)
        yield
        await session_manager.close()
        RedisClient().clear()


@pytest_asyncio.fixture(autouse=True)
async def create_tables(connection_test):
    async with session_manager.connect() as connection:
        await session_manager.drop_all(connection)
        await session_manager.create_all(connection)

        # Creating roles
        roles = [
            {"id": uuid4(), "name": role.name, "description": role.value}
            for role in RoleEnum
        ]
        stmt = text(
            """INSERT INTO roles(id, name, description) VALUES(:id, :name, :description)"""
        )
        for role in roles:
            await connection.execute(stmt, role)

        # Creating images
        images = [
            {
                "id": uuid4(),
                "name": default_avatar_data["name"],
                "size": default_avatar_data["size"],
                "location": default_avatar_data["location"],
            }
        ]
        stmt = text(
            """INSERT INTO images(id, name, size, location) VALUES(:id, :name, :size, :location)"""
        )
        for image in images:
            await connection.execute(stmt, image)

        # Creating superuser
        admin_role_id = [role["id"] for role in roles if role["name"] == "admin"][0]
        admin_avatar_id = [
            image["id"] for image in images if image["name"] == "default_avatar"
        ][0]
        super_user_passwd = get_password_hash(settings.SUPER_USER_PASSWORD)
        time_now = datetime.now()
        super_user = {
            "id": uuid4(),
            "username": "super_user",
            "hashed_password": super_user_passwd,
            "role_id": admin_role_id,
            "created_at": time_now,
            "updated_at": time_now,
            "avatar_id": admin_avatar_id,
        }
        stmt = text(
            """INSERT INTO users(id, username, hashed_password, role_id, created_at, updated_at, avatar_id) 
               VALUES(:id, :username, :hashed_password, :role_id, :created_at, :updated_at, :avatar_id)"""
        )
        await connection.execute(stmt, super_user)


@pytest_asyncio.fixture(autouse=True)
async def session_override(app, connection_test):
    async def get_db_override():
        async with session_manager.session() as session:
            yield session

    app.dependency_overrides[get_db] = get_db_override


@pytest_asyncio.fixture
async def create_user(client: AsyncClient):
    response = await client.post("/users", json=user_data)
    return response.json()


@pytest_asyncio.fixture
async def authorize(client: AsyncClient) -> dict[str, str]:
    response = await client.post("/auth/login", json=user_data)
    tokens = response.json()
    return tokens


@pytest_asyncio.fixture
async def authorize_admin(client: AsyncClient) -> dict[str, str]:
    response = await client.post("/auth/login", json=admin_data)
    tokens = response.json()
    return tokens


@pytest_asyncio.fixture
async def authorization_header(authorize):
    return {"Authorization": f'Bearer {authorize["access_token"]}'}


@pytest_asyncio.fixture
async def authorization_header_admin(authorize_admin):
    return {"Authorization": f'Bearer {authorize_admin["access_token"]}'}
