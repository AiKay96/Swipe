from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from src.runner.db import Base

from src.runner.config import settings
from src.infra.models.user import User
from src.infra.models.token import Token
from src.infra.models.user import User
from src.infra.models.token import Token
from src.infra.models.personal_post.post import PersonalPost
from src.infra.models.personal_post.comment import PersonalComment
from src.infra.models.personal_post.like import PersonalLike
from src.infra.models.personal_post.media import PersonalMedia

from src.infra.models.creator_post.post import Post as CreatorPost
from src.infra.models.creator_post.comment import Comment as CreatorPostComment
from src.infra.models.creator_post.like import Like as CreatorPostLike
from src.infra.models.creator_post.media import Media as CreatorPostMedia
from src.infra.models.creator_post.hashtag import Hashtag as CreatorPostHashtag
from src.infra.models.creator_post.save import Save as CreatorPostSave
from src.infra.models.creator_post.category_tag import CategoryTag
from src.infra.models.creator_post.reference import Reference
from src.infra.models.creator_post.category import Category
from src.infra.models.creator_post.feed_preference import FeedPreference
from src.infra.models.creator_post.post_interaction import PostInteraction
from src.infra.models.friend import Friend
from src.infra.models.friend import FriendRequest
from src.infra.models.friend import SuggestionSkip
from src.infra.models.follow import Follow
from src.infra.models.messenger import Message, Chat

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name :
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
