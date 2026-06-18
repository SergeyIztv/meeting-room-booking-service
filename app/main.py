from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.api.endpoints.admin import router as admin_router
from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.bookings import router as bookings_router
from app.api.endpoints.rooms import router as rooms_router
from app.core.database import Base, engine
from app.core.exceptions import ServiceException
from app.schemas.error import ErrorResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="Meeting Room Booking Service", lifespan=lifespan)


@app.exception_handler(ServiceException)
async def service_exception_handler(request: Request, exc: ServiceException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(code=exc.code, detail=exc.detail).model_dump(),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict):
        content = ErrorResponse(**exc.detail).model_dump()
    else:
        content = ErrorResponse(code="ERROR", detail=str(exc.detail)).model_dump()
    return JSONResponse(status_code=exc.status_code, content=content)


app.include_router(auth_router, prefix="/auth")
app.include_router(admin_router)
app.include_router(rooms_router)
app.include_router(bookings_router)
