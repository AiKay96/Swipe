import os
from typing import Any

import pytest
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.infra.fastapi.auth import auth_api
from src.infra.fastapi.users import user_api
from src.infra.models.post.personal_post import PersonalPost  # noqa: F401
from src.infra.models.post.post_comment import PostComment  # noqa: F401
from src.infra.models.post.post_like import PostLike  # noqa: F401
from src.infra.models.post.post_media import PostMedia  # noqa: F401
from src.infra.repositories.tokens import TokenRepository
from src.infra.repositories.users import UserRepository
from src.runner.db import Base
from src.runner.setup import get_db

load_dotenv()
DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql://admin:admin@localhost:5432/swipe_test"
)
engine = create_engine(DATABASE_URL, future=True)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture(scope="session", autouse=True)
def setup_db() -> Any:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session() -> Any:
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session) -> TestClient:
    app = FastAPI()

    app.include_router(user_api)
    app.include_router(auth_api)
    app.dependency_overrides[get_db] = lambda: db_session
    app.state.users = UserRepository(db_session)
    app.state.tokens = TokenRepository(db_session)

    return TestClient(app)
