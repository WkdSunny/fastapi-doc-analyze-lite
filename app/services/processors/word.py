# /app/services/processors/word.py
"""
This module defines the Word processing logic using python-docx.
"""

import json
import asyncio
from docx import Document
from app.config import logger

async def useDocX(file_path):
    try:
        document = await asyncio.to_thread(Document, file_path)
        paragraphs = [p.text for p in document.paragraphs]
        json_data = {
            'paragraphs': paragraphs
        }
        return json.dumps(json_data)

    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise

    except Exception as e:
        logger.error(f"Failed to process Word file {file_path}: {e}")
        raise
