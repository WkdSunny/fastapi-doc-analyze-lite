# /app/utils/file_utils.py

import aiofiles
import filetype
from fastapi import UploadFile, Request, HTTPException
from typing import List, Dict, Any
from app.utils.api_utils import AsyncAPIClient
from app.utils.json_utils import serialize
from app.config import settings, logger, get_base_url

database = settings.database

async def save_temp_file(file: UploadFile) -> str:
    """
    Save the uploaded file to a temporary path asynchronously.
    """
    temp_path = f"/tmp/{file.filename}"
    async with aiofiles.open(temp_path, 'wb') as temp_file:
        await temp_file.write(await file.read())
    return temp_path

async def get_file_type(file: UploadFile) -> str:
    kind = filetype.guess(await file.read(2048))
    await file.seek(0)
    return kind.mime if kind else None