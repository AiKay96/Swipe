from collections.abc import Generator

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.infra.fastapi.auth import auth_api
from src.infra.fastapi.personal_posts import personal_post_api
from src.infra.fastapi.social import social_api
from src.infra.fastapi.users import user_api
from src.infra.repositories.personal_post.comments import (
    CommentRepository as PersonalPostCommentRepository,
)
from src.infra.repositories.personal_post.likes import (
    LikeRepository as PersonalPostLikeRepository,
)
from src.infra.repositories.personal_post.posts import PostRepository
from src.infra.repositories.social import FollowRepository, FriendRepository
from src.infra.repositories.tokens import TokenRepository
from src.infra.repositories.users import UserRepository
from src.infra.services.personal_post import PersonalPostService
from src.infra.services.social import SocialService
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

    db: Session = next(get_db())
    app.state.users = UserRepository(db)
    app.state.tokens = TokenRepository(db)
    app.state.personal_posts = PersonalPostService(
        PostRepository(db),
        PersonalPostLikeRepository(db),
        PersonalPostCommentRepository(db),
    )
    app.state.social = SocialService(
        FollowRepository(db),
        FriendRepository(db),
        app.state.users,
    )

    app.include_router(user_api)
    app.include_router(auth_api)
    app.include_router(personal_post_api)
    app.include_router(social_api)

    return app
