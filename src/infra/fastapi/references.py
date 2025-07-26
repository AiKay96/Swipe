from uuid import UUID

from fastapi import APIRouter, UploadFile
from fastapi.responses import JSONResponse

from src.core.errors import DoesNotExistError
from src.infra.fastapi.dependables import (
    ReferenceServiceDependable,
)

reference_api = APIRouter(tags=["Reference"])


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
