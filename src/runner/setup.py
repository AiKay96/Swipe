from collections.abc import Generator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.infra.fastapi.auth import auth_api
from src.infra.fastapi.feed import feed_api
from src.infra.fastapi.personal_posts import personal_post_api
from src.infra.fastapi.references import reference_api
from src.infra.fastapi.social import social_api
from src.infra.fastapi.users import user_api
from src.infra.models.creator_post.comment import (
    Comment as CreatorComment,  # noqa: F401
)
from src.infra.models.creator_post.hashtag import Hashtag  # noqa: F401
from src.infra.models.creator_post.like import Like as CreatorLike  # noqa: F401
from src.infra.models.creator_post.media import Media as CreatorMedia  # noqa: F401
from src.infra.models.creator_post.post import Post as CreatorPost  # noqa: F401
from src.infra.models.creator_post.save import Save as CreatorSave  # noqa: F401
from src.infra.repositories.creator_post.categories import CategoryRepository
from src.infra.repositories.creator_post.references import ReferenceRepository
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
from src.infra.services.feed import FeedService
from src.infra.services.personal_post import PersonalPostService
from src.infra.services.reference import ReferenceService
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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    db: Session = next(get_db())

    user_repo = UserRepository(db)
    app.state.tokens = TokenRepository(db)

    post_repo = PostRepository(db)
    personal_post_like_repo = PersonalPostLikeRepository(db)
    personal_post_comment_repo = PersonalPostCommentRepository(db)

    follow_repo = FollowRepository(db)
    friend_repo = FriendRepository(db)
    token_repo = TokenRepository(db)

    reference_repo = ReferenceRepository(db)
    category_repo = CategoryRepository(db)

    app.state.users = user_repo
    app.state.tokens = token_repo

    app.state.personal_posts = PersonalPostService(
        post_repo=post_repo,
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
        post_repo=post_repo,
        friend_repo=friend_repo,
        like_repo=personal_post_like_repo,
    )
    app.state.references = ReferenceService(
        reference_repo=reference_repo,
        category_repo=category_repo,
    )

    app.include_router(user_api)
    app.include_router(auth_api)
    app.include_router(personal_post_api)
    app.include_router(social_api)
    app.include_router(feed_api)
    app.include_router(reference_api)

    return app
