# word.py
"""
This module defines the Word processing task using python-docx.
"""

import json
import asyncio
from docx import Document
from celery import shared_task
from app.config import logger
from app.utils.async_utils import run_async_task


@shared_task
def useDocX(file_path):
    """
    Asynchronously processes a Word document and converts it to JSON format.

    Args:
    file_path (str): The path to the Word document to be processed.

    Returns:
    str: JSON string representation of the Word document's paragraphs.
    """
    try:
        result = run_async_task(_useDocX, file_path)
        return result
    except Exception as e:
        logger.error(f"Failed to process Word file {file_path}: {e}")
        return json.dumps({'paragraphs': []})  # Return empty paragraphs list in case of failure

async def _useDocX(file_path):
    try:
        # Use asyncio.to_thread to run the blocking operation in a separate thread
        document = await asyncio.to_thread(Document, file_path)
        paragraphs = [p.text for p in document.paragraphs]
        json_data = {
            'paragraphs': paragraphs
        }
        return json.dumps(json_data)
    except Exception as e:
        logger.error(f"Failed to process Word file {file_path}: {e}")
        return json.dumps({'paragraphs': []})  # Return empty paragraphs list in case of failure

# Example usage:
if __name__ == "__main__":
    path = "path_to_your_word_file.docx"
    results = asyncio.run(useDocX(path))
    print(results)
