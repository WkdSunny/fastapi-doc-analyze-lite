from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette.middleware.authentication import AuthenticationMiddleware
from app.routers import convert, extract_openai, extract_claude
from app.dependencies import verify_token
from config import logger  # Import the logger from config

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/")
async def root():
    logger.info("Root endpoint called")  # Log when this endpoint is accessed
    return {"message": "Welcome to the PDF Processing API"}

# Include routers with logging
app.include_router(convert.router, dependencies=[Depends(verify_token)])
app.include_router(extract_openai.router, dependencies=[Depends(verify_token)])
app.include_router(extract_claude.router, dependencies=[Depends(verify_token)])

@app.exception_handler(Exception)
async def universal_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc} - Request details: {request.url.path}")
    return {"message": "An internal error occurred", "details": str(exc)}
