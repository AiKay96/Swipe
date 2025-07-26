from dataclasses import dataclass
from typing import IO, Any, Protocol
from uuid import UUID


@dataclass
class Reference:
    title: str
    description: str
    image_url: str
    tag_names: list[str]
    attributes: dict[str, Any]


class ReferenceService(Protocol):
    def create_many_categories_from_file(
        self, file: IO[bytes], file_type: str
    ) -> None: ...

    def create_many_references_from_file(
        self, file: IO[bytes], file_type: str, category_id: UUID
    ) -> None: ...
