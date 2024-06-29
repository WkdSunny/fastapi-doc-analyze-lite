"""
This module defines the Excel processing task using OpenPyXL.
"""

from app.tasks.celery_config import app
import openpyxl
import json
from app.config import logger
import asyncio

@app.task
async def useOpenPyXL(file_path):
    """
    Asynchronously processes an Excel file and converts it to JSON format.

    Args:
    file_path (str): The path to the Excel file to be processed.

    Returns:
    str: JSON string representation of the Excel data.
    """
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
            json_row = {}
            for i, value in enumerate(row):
                json_row[headers[i]] = value
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
