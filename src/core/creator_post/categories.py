from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class Category:
    name: str
    tag_names: list[str]
    id: UUID = field(default_factory=uuid4)
