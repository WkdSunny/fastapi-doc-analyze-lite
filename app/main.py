# /app/main.py
"""
This module defines the main FastAPI application.
"""

import os
import sys
from fastapi import FastAPI, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from starlette.middleware.authentication import AuthenticationMiddleware
from app.routers import convert
from app.routers import retrieve
from app.routers import questions
from app.routers.extract import openai, claude
from app.dependencies import verify_token
from app.config import logger, init_db

# Add the project root directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/")
async def root(request: Request):
    logger.info(f"Host: {request.client.host}")
    logger.info(f"URL: {request.url}")
    logger.info("Root endpoint called")  # Log when this endpoint is accessed
    return {"message": "Welcome to the PDF Processing API"}

# Include routers with logging
app.include_router(convert.router, dependencies=[Depends(verify_token)])
app.include_router(retrieve.router, dependencies=[Depends(verify_token)])
app.include_router(questions.router, dependencies=[Depends(verify_token)])
app.include_router(openai.router, dependencies=[Depends(verify_token)])
app.include_router(claude.router, dependencies=[Depends(verify_token)])

@app.exception_handler(Exception)
async def universal_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc} - Request details: {request.url.path}")
    return {"message": "An internal error occurred", "details": str(exc)}

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    await init_db()
    logger.info("Database initialized and collections checked")
