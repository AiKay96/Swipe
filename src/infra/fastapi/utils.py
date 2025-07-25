from fastapi.responses import JSONResponse

from src.core.errors import DoesNotExistError, ExistsError


def exception_response(e: Exception) -> JSONResponse:
    if isinstance(e, DoesNotExistError):
        return JSONResponse(status_code=404, content={"message": "Resource not found."})
    if isinstance(e, ExistsError):
        return JSONResponse(
            status_code=409, content={"message": "Conflict: Already exists."}
        )
    return JSONResponse(status_code=500, content={"message": str(e)})
