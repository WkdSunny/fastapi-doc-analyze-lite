# muPDF.py
"""
This module defines the PDF processing task using PyMuPDF (MuPDF).
"""

import fitz
import asyncio
from celery import shared_task
from app.models.pdf_model import BoundingBox, PDFTextResponse, coordinates
from app.utils.async_utils import run_async_task
from app.config import logger

@shared_task
def usePyMuPDF(file_path):
    """
    Extracts text and bounding boxes from a readable PDF using PyMuPDF (MuPDF).

    Args:
    file_path (str): The path to the PDF file to be processed.

    Returns:
    dict: Contains the file name, concatenated text, and bounding boxes.
    """
    try:
        result = run_async_task(_usePyMuPDF, file_path)
        return result
    except Exception as e:
        logger.error(f"Failed to process PDFs with PyMuPDF: {e}")
        return PDFTextResponse(file_name=file_path, text="", bounding_boxes=[]).to_dict()

async def _usePyMuPDF(file_path):
    try:
        text_and_boxes = []

        # Use asyncio.to_thread to run the blocking operation in a separate thread
        doc = await asyncio.to_thread(fitz.open, file_path)
        for page_number, page in enumerate(doc, start=1):
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if block['type'] == 0:  # Text block
                    text = "".join([line['text'] for line in block['lines']])
                    bbox = BoundingBox(
                        page=page_number,
                        bbox=coordinates(
                            left=float(block['bbox'][0]),
                            top=float(block['bbox'][1]),
                            width=float(block['bbox'][2]) - float(block['bbox'][0]),
                            height=float(block['bbox'][3]) - float(block['bbox'][1])
                        ),
                        text=text.strip(),
                        confidence=1.0  # Assuming confidence if not provided
                    )
                    text_and_boxes.append(bbox)
        doc.close()

        response = PDFTextResponse(
            file_name=file_path,
            text="\n".join([bbox.text for bbox in text_and_boxes]),
            bounding_boxes=text_and_boxes
        )
        logger.info(f"Successfully extracted text and bounding boxes from {file_path}")
        return response.to_dict()

    except Exception as e:
        logger.error(f"Failed to extract from PDF using PyMuPDF: {e}")
        return PDFTextResponse(file_name=file_path, text="", bounding_boxes=[]).to_dict()

# Example usage:
if __name__ == "__main__":
    path = "path_to_your_pdf_file.pdf"
    results = asyncio.run(usePyMuPDF(path))
    print(results)
