# pyPDF2.py
"""
This module defines the PDF processing task using PyPDF2.
"""

from app.tasks.celery_config import app
from PyPDF2 import PdfReader
from app.models.pdf_model import PDFTextResponse, BoundingBox
from app.config import logger
import asyncio  # Import asyncio for async support

@app.task
async def usePyPDF2(file_path):
    """
    Asynchronously extracts text from a readable PDF using PyPDF2.
    Note: PyPDF2 does not provide bounding box information.

    Args:
    file_path (str): The path to the PDF file to be processed.

    Returns:
    PDFTextResponse: Contains the file name, concatenated text, and bounding boxes (None in this case).
    """
    try:
        text_and_boxes = []
        # Use asyncio.to_thread to run the blocking operation in a separate thread
        reader = await asyncio.to_thread(PdfReader, file_path)
        for page_number, page in enumerate(reader.pages, start=1):
            text = await asyncio.to_thread(page.extract_text)
            # PyPDF2 does not provide bounding box information directly
            bbox = BoundingBox(
                page=page_number,
                bbox=None,
                text=text.strip() if text else ""
            )
            text_and_boxes.append(bbox)
        return PDFTextResponse(file_name=file_path, text="\n".join([bbox.text for bbox in text_and_boxes]), bounding_boxes=text_and_boxes)
    except Exception as e:
        logger.error(f"Failed to extract from PDF using PyPDF2: {e}")
        return PDFTextResponse(file_name=file_path, text="", bounding_boxes=[])

# Example usage:
if __name__ == "__main__":
    path = "path_to_your_pdf_file.pdf"
    # Use asyncio.run to execute the async function
    results = asyncio.run(usePyPDF2(path))
    print(results)