from collections.abc import Generator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.infra.decorators.post import PostDecorator
from src.infra.fastapi.auth import auth_api
from src.infra.fastapi.creator_posts import creator_post_api
from src.infra.fastapi.feed import feed_api
from src.infra.fastapi.media import media_api
from src.infra.fastapi.messenger import messenger_api
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
from src.infra.repositories.creator_post.feed_preferences import (
    FeedPreferenceRepository,
)
from src.infra.repositories.creator_post.likes import (
    LikeRepository as CreatorPostLikeRepository,
)
from src.infra.repositories.creator_post.post_interactions import (
    PostInteractionRepository,
)
from src.infra.repositories.creator_post.posts import (
    PostRepository as CreatorPostRepository,
)
from src.infra.repositories.creator_post.references import ReferenceRepository
from src.infra.repositories.creator_post.saves import SaveRepository
from src.infra.repositories.messenger import ChatRepository, MessageRepository
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
from src.infra.services.messenger import MessengerService
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
    app.mount("/media", StaticFiles(directory=str(settings.media_root)), name="media")

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

    personal_post_repo = PersonalPostRepository(db)
    personal_post_like_repo = PersonalPostLikeRepository(db)
    personal_post_comment_repo = PersonalPostCommentRepository(db)

    follow_repo = FollowRepository(db)
    friend_repo = FriendRepository(db)
    token_repo = TokenRepository(db)

    creator_post_repo = CreatorPostRepository(db)
    reference_repo = ReferenceRepository(db)
    category_repo = CategoryRepository(db)
    creator_post_like_repo = CreatorPostLikeRepository(db)
    creator_post_comment_repo = CreatorPostCommentRepository(db)
    save_repo = SaveRepository(db)
    feed_pref_repo = FeedPreferenceRepository(db)
    post_init_repo = PostInteractionRepository(db)
    chat_repo = ChatRepository(db)
    message_repo = MessageRepository(db)

    app.state.users = user_repo
    app.state.tokens = token_repo

    post_decorator = PostDecorator(
        personal_post_like_repo=personal_post_like_repo,
        save_repo=save_repo,
        creator_post_like_repo=creator_post_like_repo,
    )

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
        feed_pref_repo=feed_pref_repo,
        category_repo=category_repo,
    )
    app.state.feed = FeedService(
        personal_post_repo=personal_post_repo,
        friend_repo=friend_repo,
        preference_repo=feed_pref_repo,
        post_interaction_repo=post_init_repo,
        follow_repo=follow_repo,
        post_repo=creator_post_repo,
        post_decorator=post_decorator,
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
        feed_pref_repo=feed_pref_repo,
    )
    app.state.messenger = MessengerService(
        chat_repo=chat_repo,
        message_repo=message_repo,
    )

    app.include_router(user_api)
    app.include_router(auth_api)
    app.include_router(personal_post_api)
    app.include_router(creator_post_api)
    app.include_router(social_api)
    app.include_router(feed_api)
    app.include_router(reference_api)
    app.include_router(media_api)
    app.include_router(messenger_api)

    return app
