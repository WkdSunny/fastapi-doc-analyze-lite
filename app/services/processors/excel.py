# excel.py
"""
This module defines the Excel processing task using OpenPyXL.
"""
import json
import asyncio
import openpyxl
from celery import shared_task
from app.config import logger
from app.utils.async_utils import run_async_task

@shared_task
def useOpenPyXL(file_path):
    """
    Asynchronously processes an Excel file and converts it to JSON format.

    Args:
    file_path (str): The path to the Excel file to be processed.

    Returns:
    str: JSON string representation of the Excel data.
    """
    try:
        result = run_async_task(_useOpenPyXL, file_path)
        return result
    except Exception as e:
        logger.error(f"Failed to process Excel file {file_path}: {e}")
        return json.dumps([])  # Return empty JSON array in case of failure

async def _useOpenPyXL(file_path):
    try:
        # Use asyncio.to_thread to run the blocking operation in a separate thread
        workbook = await asyncio.to_thread(openpyxl.load_workbook, file_path)
        worksheet = workbook.active

        data = []
        for row in worksheet.iter_rows(values_only=True):
            data.append(row)

        headers = data[0]
        json_data = []
        for row in data[1:]:
            json_row = {headers[i]: value for i, value in enumerate(row)}
            json_data.append(json_row)

        return json.dumps(json_data)
    except Exception as e:
        logger.error(f"Failed to process Excel file {file_path}: {e}")
        return json.dumps([])  # Return empty JSON array in case of failure

# Example usage:
if __name__ == "__main__":
    path = "path_to_your_excel_file.xlsx"
    results = asyncio.run(useOpenPyXL(path))
    print(results)
