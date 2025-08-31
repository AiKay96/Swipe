from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer

from src.core.creator_post.posts import CreatorPostService
from src.core.creator_post.references import ReferenceService
from src.core.feed import FeedService
from src.core.personal_post.posts import PersonalPostService
from src.core.search import SearchService
from src.core.social import SocialService
from src.core.tokens import TokenRepository
from src.core.users import User, UserRepository
from src.infra.services.auth import AuthService


def get_user_repository(request: Request) -> UserRepository:
    return request.app.state.users  # type: ignore


UserRepositoryDependable = Annotated[UserRepository, Depends(get_user_repository)]


def get_token_repository(request: Request) -> TokenRepository:
    return request.app.state.tokens  # type: ignore


TokenRepositoryDependable = Annotated[TokenRepository, Depends(get_token_repository)]


def get_personal_post_service(request: Request) -> PersonalPostService:
    return request.app.state.personal_posts  # type: ignore


PersonalPostServiceDependable = Annotated[
    PersonalPostService, Depends(get_personal_post_service)
]


def get_creator_post_service(request: Request) -> CreatorPostService:
    return request.app.state.creator_posts  # type: ignore


CreatorPostServiceDependable = Annotated[
    CreatorPostService, Depends(get_creator_post_service)
]


def get_social_service(request: Request) -> SocialService:
    return request.app.state.social  # type: ignore


SocialServiceDependable = Annotated[SocialService, Depends(get_social_service)]


def get_feed_service(request: Request) -> FeedService:
    return request.app.state.feed  # type: ignore


FeedServiceDependable = Annotated[FeedService, Depends(get_feed_service)]


def get_reference_service(request: Request) -> ReferenceService:
    return request.app.state.references  # type: ignore


ReferenceServiceDependable = Annotated[ReferenceService, Depends(get_reference_service)]


def get_search_service(request: Request) -> SearchService:
    return request.app.state.searchs  # type: ignore


SearchServiceDependable = Annotated[SearchService, Depends(get_search_service)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth")


def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
) -> User:
    auth = AuthService(get_user_repository(request), get_token_repository(request))
    try:
        return auth.get_user_from_token(token)
    except Exception as err:
        raise HTTPException(status_code=401, detail=str(err)) from err


def get_refresh_token(request: Request) -> str:
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing.")
    return refresh_token
