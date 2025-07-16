from collections.abc import Generator

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.infra.fastapi.auth import auth_api
from src.infra.fastapi.users import user_api
from src.infra.repositories.users import UserRepository
from src.runner.config import settings
from src.runner.db import Base

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_app() -> FastAPI:
    Base.metadata.create_all(bind=engine)

    app = FastAPI()
    app.include_router(user_api)
    app.include_router(auth_api)

    db: Session = next(get_db())
    app.state.users = UserRepository(db)

    return app
