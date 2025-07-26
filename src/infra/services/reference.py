from dataclasses import dataclass
from typing import IO
from uuid import UUID

import pandas as pd

from src.core.creator_post.categories import Category
from src.core.creator_post.references import Reference
from src.infra.repositories.creator_post.categories import CategoryRepository
from src.infra.repositories.creator_post.references import ReferenceRepository


@dataclass
class ReferenceService:
    category_repo: CategoryRepository
    reference_repo: ReferenceRepository

    def create_many_categories_from_file(self, file: IO[bytes], file_type: str) -> None:
        df = self._load_file(file, file_type)
        categories: list[Category] = []
        for _, row in df.iterrows():
            tag_names = [tag.strip() for tag in row["tags"].split(",") if tag.strip()]
            categories.append(Category(name=row["name"], tag_names=tag_names))
        self.category_repo.create_many(categories)

    def create_many_references_from_file(
        self, file: IO[bytes], file_type: str, category_id: UUID
    ) -> None:
        df = self._load_file(file, file_type)
        references: list[Reference] = []
        for _, row in df.iterrows():
            tag_names = [tag.strip() for tag in row["tags"].split(",") if tag.strip()]
            metadata = {}
            for column in row.index:
                if column not in {"title", "description", "image_url", "tags"}:
                    value = row[column]
                    if pd.notna(value):
                        metadata[column] = value

            references.append(
                Reference(
                    title=row["title"],
                    description=row.get("description", ""),
                    image_url=row.get("image_url", ""),
                    tag_names=tag_names,
                    attributes=metadata,
                )
            )

        self.reference_repo.create_many(category_id, references)

    def _load_file(self, file: IO[bytes], file_type: str) -> pd.DataFrame:
        if file_type == "csv":
            return pd.read_csv(file)
        if file_type in {"xls", "xlsx"}:
            return pd.read_excel(file, engine="openpyxl")
        raise ValueError("Unsupported file type")
