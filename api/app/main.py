"""
Main application module.
"""
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .config import settings
from .routes import router as api_router
from .errors import NoodleError, ErrorType

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_PREFIX}/openapi.json"
)

# Exception handlers
@app.exception_handler(NoodleError)
async def noodle_error_handler(request: Request, exc: NoodleError):
    """Handle NoodleError exceptions."""
    status_code = status.HTTP_400_BAD_REQUEST
    
    # Map error types to status codes
    if exc.error_type == ErrorType.VALIDATION:
        status_code = status.HTTP_400_BAD_REQUEST
    elif exc.error_type == ErrorType.NOT_FOUND:
        status_code = status.HTTP_404_NOT_FOUND
    elif exc.error_type == ErrorType.PERMISSION:
        status_code = status.HTTP_403_FORBIDDEN
    elif exc.error_type == ErrorType.DATABASE:
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif exc.error_type == ErrorType.SERVICE_ERROR:
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle FastAPI HTTPException."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle FastAPI validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)}
    )

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(
    api_router,
    prefix=settings.API_PREFIX
)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
