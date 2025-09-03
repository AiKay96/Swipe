from dataclasses import dataclass, field
from typing import IO, Any, Protocol
from uuid import UUID, uuid4

from src.core.creator_post.categories import Category


@dataclass
class Reference:
    title: str
    description: str
    image_url: str
    tag_names: list[str]
    attributes: dict[str, Any]
    category_id: UUID | None = None
    category_name: str | None = None
    id: UUID = field(default_factory=uuid4)


class ReferenceService(Protocol):
    def create_many_categories_from_file(
        self, file: IO[bytes], file_type: str
    ) -> None: ...

    def create_many_references_from_file(
        self, file: IO[bytes], file_type: str, category_id: UUID
    ) -> None: ...

    def get_categories(self) -> list[Category]: ...

    def get_references_by_category(self, category_id: UUID) -> list[Reference]: ...

    def get_reference(self, reference_id: UUID) -> Reference | None: ...
