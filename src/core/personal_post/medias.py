from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol
from uuid import UUID, uuid4


class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"


@dataclass
class Media:
    post_id: UUID
    url: str
    media_type: MediaType
    id: UUID = field(default_factory=uuid4)


class MediaRepository(Protocol):
    def create(self, media: Media) -> Media: ...
    def list_by_post(self, post_id: UUID) -> list[Media]: ...
    def delete(self, media_id: UUID) -> None: ...
