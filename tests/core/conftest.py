import os
from typing import Any

import pytest
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.infra.fastapi.auth import auth_api
from src.infra.fastapi.creator_posts import creator_post_api
from src.infra.fastapi.feed import feed_api
from src.infra.fastapi.personal_posts import personal_post_api
from src.infra.fastapi.references import reference_api
from src.infra.fastapi.social import social_api
from src.infra.fastapi.users import user_api
from src.infra.models.creator_post.hashtag import Hashtag  # noqa: F401
from src.infra.models.creator_post.media import Media as CreatorMedia  # noqa: F401
from src.infra.models.personal_post.media import (
    PersonalMedia as PersonalMedia,  # noqa: F401
)
from src.infra.repositories.creator_post.categories import CategoryRepository
from src.infra.repositories.creator_post.comments import (
    CommentRepository as CreatorPostCommentRepository,
)
from src.infra.repositories.creator_post.likes import (
    LikeRepository as CreatorPostLikeRepository,
)
from src.infra.repositories.creator_post.posts import (
    PostRepository as CreatorPostRepository,
)
from src.infra.repositories.creator_post.references import ReferenceRepository
from src.infra.repositories.creator_post.saves import SaveRepository
from src.infra.repositories.personal_post.comments import (
    CommentRepository as PersonalPostCommentRepository,
)
from src.infra.repositories.personal_post.likes import (
    LikeRepository as PersonalPostLikeRepository,
)
from src.infra.repositories.personal_post.posts import (
    PostRepository as PersonalPostRepository,
)
from src.infra.repositories.social import FollowRepository, FriendRepository
from src.infra.repositories.tokens import TokenRepository
from src.infra.repositories.users import UserRepository
from src.infra.services.creator_post import CreatorPostService
from src.infra.services.feed import FeedService
from src.infra.services.personal_post import PersonalPostService
from src.infra.services.reference import ReferenceService
from src.infra.services.social import SocialService
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

    app.dependency_overrides[get_db] = lambda: db_session
    user_repo = UserRepository(db_session)
    app.state.tokens = TokenRepository(db_session)

    personal_post_repo = PersonalPostRepository(db_session)
    personal_post_like_repo = PersonalPostLikeRepository(db_session)
    personal_post_comment_repo = PersonalPostCommentRepository(db_session)

    follow_repo = FollowRepository(db_session)
    friend_repo = FriendRepository(db_session)
    token_repo = TokenRepository(db_session)

    creator_post_repo = CreatorPostRepository(db_session)
    reference_repo = ReferenceRepository(db_session)
    category_repo = CategoryRepository(db_session)
    creator_post_like_repo = CreatorPostLikeRepository(db_session)
    creator_post_comment_repo = CreatorPostCommentRepository(db_session)
    save_repo = SaveRepository(db_session)

    app.state.users = user_repo
    app.state.tokens = token_repo

    app.state.personal_posts = PersonalPostService(
        post_repo=personal_post_repo,
        like_repo=personal_post_like_repo,
        comment_repo=personal_post_comment_repo,
        friend_repo=friend_repo,
    )
    app.state.social = SocialService(
        follow_repo=follow_repo,
        friend_repo=friend_repo,
        user_repo=user_repo,
    )
    app.state.feed = FeedService(
        post_repo=personal_post_repo,
        friend_repo=friend_repo,
        like_repo=personal_post_like_repo,
    )
    app.state.references = ReferenceService(
        reference_repo=reference_repo,
        category_repo=category_repo,
    )
    app.state.creator_posts = CreatorPostService(
        post_repo=creator_post_repo,
        like_repo=creator_post_like_repo,
        comment_repo=creator_post_comment_repo,
        save_repo=save_repo,
    )

    app.include_router(user_api)
    app.include_router(auth_api)
    app.include_router(personal_post_api)
    app.include_router(creator_post_api)
    app.include_router(social_api)
    app.include_router(feed_api)
    app.include_router(reference_api)
    return TestClient(app)
