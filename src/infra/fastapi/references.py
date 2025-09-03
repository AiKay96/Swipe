from typing import Any
from uuid import UUID

from fastapi import APIRouter, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.core.creator_post.categories import Category
from src.core.creator_post.references import Reference
from src.core.errors import DoesNotExistError
from src.infra.fastapi.dependables import (
    ReferenceServiceDependable,
)

reference_api = APIRouter(tags=["Reference"])


class CategoryItem(BaseModel):
    id: UUID
    name: str
    tags: list[str]

    @classmethod
    def from_category(cls, c: Category) -> "CategoryItem":
        return cls(id=c.id, name=c.name, tags=list(c.tag_names))


class CategoryListEnvelope(BaseModel):
    categories: list[CategoryItem]


class ReferenceItem(BaseModel):
    id: UUID
    category_id: UUID | None
    title: str
    description: str
    image_url: str | None
    tags: list[str]
    attributes: dict[str, Any]

    @classmethod
    def from_reference(cls, r: Reference) -> "ReferenceItem":
        return cls(
            id=r.id,
            category_id=r.category_id,
            title=r.title,
            description=r.description,
            image_url=r.image_url,
            tags=list(r.tag_names),
            attributes=dict(r.attributes),
        )


class ReferenceEnvelope(BaseModel):
    reference: ReferenceItem


class ReferenceListEnvelope(BaseModel):
    references: list[ReferenceItem]


@reference_api.post("/reference/categories/import", status_code=201)
def import_categories(
    service: ReferenceServiceDependable,
    file: UploadFile,
) -> JSONResponse:
    try:
        assert file.filename
        service.create_many_categories_from_file(
            file.file, file.filename.split(".")[-1]
        )
        return JSONResponse(
            status_code=201, content={"message": "Categories imported successfully."}
        )
    except Exception as e:
        return JSONResponse(status_code=400, content={"message": str(e)})


@reference_api.post("/reference/{category_id}/import", status_code=201)
def import_references(
    category_id: UUID,
    service: ReferenceServiceDependable,
    file: UploadFile,
) -> JSONResponse:
    try:
        assert file.filename
        service.create_many_references_from_file(
            file.file, file.filename.split(".")[-1], category_id
        )
        return JSONResponse(
            status_code=201, content={"message": "References imported successfully."}
        )
    except DoesNotExistError:
        return JSONResponse(status_code=404, content={"message": "Category not found."})
    except Exception as e:
        return JSONResponse(status_code=400, content={"message": str(e)})


@reference_api.get(
    "/reference/categories",
    status_code=200,
    response_model=CategoryListEnvelope,
)
def get_categories(
    service: ReferenceServiceDependable,
) -> dict[str, Any] | JSONResponse:
    try:
        cats = service.get_categories()
        return {"categories": [CategoryItem.from_category(c) for c in cats]}
    except Exception as e:
        return JSONResponse(status_code=400, content={"message": str(e)})


@reference_api.get(
    "/reference/categories/{category_id}/references",
    status_code=200,
    response_model=ReferenceListEnvelope,
)
def get_references_by_category(
    category_id: UUID,
    service: ReferenceServiceDependable,
) -> dict[str, Any] | JSONResponse:
    try:
        refs = service.get_references_by_category(category_id)
        return {"references": [ReferenceItem.from_reference(r) for r in refs]}
    except Exception as e:
        return JSONResponse(status_code=400, content={"message": str(e)})


@reference_api.get(
    "/reference/references/{reference_id}",
    status_code=200,
    response_model=ReferenceEnvelope,
)
def get_reference(
    reference_id: UUID,
    service: ReferenceServiceDependable,
) -> dict[str, Any] | JSONResponse:
    try:
        ref = service.get_reference(reference_id)
        if ref is None:
            return JSONResponse(status_code=404, content={"message": "Not found."})
        return {"reference": ReferenceItem.from_reference(ref)}
    except Exception as e:
        return JSONResponse(status_code=400, content={"message": str(e)})
