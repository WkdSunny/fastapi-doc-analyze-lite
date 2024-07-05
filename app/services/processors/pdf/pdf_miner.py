# pdf_miner.py
"""
This module defines the PDF processing task using PDFMiner.
"""

import asyncio
from celery import shared_task
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
from app.config import logger
from app.utils.async_utils import run_async_task
from app.models.pdf_model import BoundingBox, PDFTextResponse, coordinates

@shared_task
def usePDFMiner(file_path):
    """
    Process a PDF file to extract text and bounding boxes using PDFMiner.

    Args:
    file_path (str): The path to the PDF file to be processed.

    Returns:
    dict: Contains the file name, concatenated text, and bounding boxes.
    """
    try:
        results = run_async_task(_usePDFMiner, file_path)
        return results
    except Exception as e:
        logger.error(f"Failed to process PDFs with PDFMiner: {e}")
        return PDFTextResponse(file_name=file_path, text="", bounding_boxes=[]).to_dict()

async def _usePDFMiner(file_path):
    """
    Asynchronously extracts text and bounding boxes from a readable PDF using PDFMiner.
    Each text block's bounding box and text content are stored.

    Args:
    file_path (str): The path to the PDF file to be processed.

    Returns:
    dict: Contains the file name, concatenated text, and bounding boxes.
    """
    try:
        text_and_boxes = []
        logger.info(f"Extracting text from PDF using PDFMiner: {file_path}")
        
        # Run extract_pages in a separate thread
        pages = await asyncio.to_thread(extract_pages, file_path)
        for page_number, page_layout in enumerate(pages, start=1):
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    # Run element.get_text() in a separate thread
                    text = await asyncio.to_thread(element.get_text)
                    bbox = BoundingBox(
                        page=page_number,
                        bbox=coordinates(
                            left=float(element.bbox[0]),
                            top=float(element.bbox[1]),
                            width=float(element.bbox[2]) - float(element.bbox[0]),
                            height=float(element.bbox[3]) - float(element.bbox[1])
                        ),
                        text=text.strip(),
                        confidence=1.0  # PDFMiner does not provide confidence, so we use a default value
                    )
                    text_and_boxes.append(bbox)
        
        response = PDFTextResponse(
            file_name=file_path,
            text="\n".join([bbox.text for bbox in text_and_boxes]),
            bounding_boxes=text_and_boxes
        )
        logger.info(f"Successfully extracted text and bounding boxes from {file_path}")
        return response.to_dict()

    except Exception as e:
        logger.error(f"Failed to extract from PDF using PDFMiner: {e}")
        return PDFTextResponse(file_name=file_path, text="", bounding_boxes=[]).to_dict()

# Example usage:
if __name__ == "__main__":
    path = "path_to_your_pdf_file.pdf"
    # Use asyncio.run to execute the async function
    results = asyncio.run(usePDFMiner(path))
    print(results)
