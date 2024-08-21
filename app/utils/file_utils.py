# /app/utils/file_utils.py
"""
This module defines utility functions for working with files.
"""

import aiofiles
import filetype
from fastapi import UploadFile

async def save_temp_file(file: UploadFile) -> str:
    """
    Save the uploaded file to a temporary path asynchronously.

    Args:
        file (UploadFile): The file to save.

    Returns:
        str: The path to the saved file.
    """
    try:
        temp_path = f"/tmp/{file.filename}"
        # Use aiofiles context manager to write the file asynchronously
        async with aiofiles.open(temp_path, 'wb') as temp_file:
            await temp_file.write(await file.read())
        return temp_path
    except Exception as e:
        raise ValueError(f"Failed to save file: {e}")

async def get_file_type(file: UploadFile) -> str:
    """
    Get the MIME type of the uploaded file asynchronously.

    Args:
        file (UploadFile): The file to check.

    Returns:
        str: The MIME type of the file.

    Raises:
        ValueError: If the file type cannot be determined.
    """
    try:
        kind = filetype.guess(await file.read(2048))
        await file.seek(0)
        return kind.mime if kind else None
    except Exception as e:
        raise ValueError(f"Failed to determine file type: {e}")
    
# Example usage:
if __name__ == "__main__":
    import asyncio
    from fastapi import UploadFile

    async def test_file_utils():
        # Create a dummy UploadFile object
        file = UploadFile(filename="test.txt")
        # Test saving the file
        temp_path = await save_temp_file(file)
        print(f"Saved file to: {temp_path}")
        # Test getting the file type
        content_type = await get_file_type(file)
        print(f"File type: {content_type}")

    asyncio.run(test_file_utils())