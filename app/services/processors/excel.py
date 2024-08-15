# /app/services/processors/excel.py
"""
This module defines the Excel processing logic using OpenPyXL.
"""

import json
import asyncio
import openpyxl
from app.config import logger

async def useOpenPyXL(file_path):
    try:
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

    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise

    except openpyxl.utils.exceptions.InvalidFileException:
        logger.error(f"Invalid Excel file format: {file_path}")
        raise

    except Exception as e:
        logger.error(f"Failed to process Excel file {file_path}: {e}")
        raise
