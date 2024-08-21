# app/services/api/convert.py

import asyncio
from typing import List
from fastapi import UploadFile, HTTPException
from app.utils.file_utils import get_file_type, save_temp_file
from app.tasks.pdf_tasks import process_pdf
from app.tasks.excel_tasks import process_excel
from app.tasks.word_tasks import process_word
from app.tasks.img_tasks import process_img
from app.services.db.insert import insert_task
from app.config import logger

async def handle_file_result(filename: str, task, content_type: str) -> dict:
    """
    Handle the result of the file processing.
    
    Args:
        filename (str): The name of the file being processed.
        task: The Celery task object representing the file processing task.
        content_type (str): The content type of the file being processed.

    Returns:
        dict: The result of the processing including document_id.

    Raises:
        ValueError: If the processing fails or times out.
    """
    try:
        result = await asyncio.wait_for(task.get(), timeout=600)  # Adjust timeout as needed
        logger.info(f"Task result for {filename}: {result}")

        if result["status"] == "success":
            return {
                "filename": filename,
                "content_type": content_type,
                "document_id": result["document_id"]
            }
        else:
            raise ValueError(f"Processing failed for {filename}: {result['error']}")
    except asyncio.TimeoutError:
        raise ValueError(f"Processing timed out for {filename}")
    except Exception as e:
        logger.error(f"Failed to handle task result for {filename}: {e}")
        raise

async def process_file(file: UploadFile) -> dict:
    """
    Process a single file based on its type and return the result.

    Args:
        file (UploadFile): The file to process.

    Returns:
        dict: The result of the processing including document_id.

    Raises:
        ValueError: If the file type is unsupported or processing fails.
    """
    try:
        logger.info(f'Processing file: {file.filename}')
        content_type = await get_file_type(file)
        if content_type is None:
            raise ValueError("Cannot determine file type")
        logger.info(f"File type: {content_type}")

        # Save the file to a temporary path
        temp_path = await save_temp_file(file)
        logger.info(f"Saved file to temporary path: {temp_path}")

        # Process file based on type
        if 'pdf' in content_type:
            logger.info(f"PDF file detected...")
            task = process_pdf.delay(temp_path)
        elif 'excel' in content_type or 'spreadsheetml' in content_type:
            logger.info(f"Excel file detected...")
            task = process_excel.delay(temp_path)
        elif 'wordprocessingml' in content_type or 'msword' in content_type:
            logger.info(f"Word file detected...")
            task = process_word.delay(temp_path)
            logger.info(f"Image file detected...")
        elif 'image' in content_type:
            task = process_img.delay(temp_path)
        else:
            logger.error(f"Unsupported file type: {file.filename}")
            raise ValueError(f"Unsupported file type: {file.filename}")

        # Handle the result of the file processing
        result = await handle_file_result(file.filename, task, content_type)
        return result

    except Exception as e:
        logger.error(f"Failed to process file {file.filename}: {e}")
        raise

async def process_files(files: List[UploadFile]) -> dict:
    """
    Process multiple files concurrently and return their results.

    Args:
        files (List[UploadFile]): The list of files to process.

    Returns:
        dict: The results of the processing including task_id and document_data.

    Raises:
        HTTPException: If no files are processed successfully.
    """
    tasks = []
    task_document_ids = []

    # Process each file concurrently
    for file in files:
        task = asyncio.create_task(process_file(file))
        tasks.append(task)

    # Run all tasks concurrently and gather results
    document_results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out successful results
    for result in document_results:
        if not isinstance(result, Exception):
            task_document_ids.append(result["document_id"])

    # Insert the Task document with all document IDs
    task_id = await insert_task(task_document_ids)

    if not document_results:
        raise HTTPException(status_code=500, detail="No files processed successfully")

    return {
        "task_id": task_id,
        "document_data": [result for result in document_results if not isinstance(result, Exception)]
    }
