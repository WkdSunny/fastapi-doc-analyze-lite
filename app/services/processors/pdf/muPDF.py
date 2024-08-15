# app/services/processors/pdf/muPDF.py

from app.tasks.celery_config import app
from app.config import logger
from app.models.pdf_model import PDFTextResponse, BoundingBox, coordinates
from app.tasks.async_tasks import run_async_task
import fitz
import asyncio

@app.task(bind=True, max_retries=3, default_retry_delay=5)
def usePyMuPDF(self, file_path):
    """
    Extracts text and bounding boxes from a readable PDF using PyMuPDF (MuPDF).
    """
    try:
        return run_async_task(_usePyMuPDF, file_path)
    except Exception as e:
        logger.error(f"Failed to extract from PDF using PyMuPDF: {e}")
        raise self.retry(exc=e)

async def _usePyMuPDF(file_path):
    """
    Extracts text and bounding boxes from a readable PDF using PyMuPDF (MuPDF) asynchronously.
    Each text block's bounding box and text content are stored.

    Args:
    file_path (str): The path to the PDF file to be processed.

    Returns:
    dict: Contains the file name, concatenated text, and bounding boxes.
    """
    try:
        text_and_boxes = []
        logger.info(f"Opening PDF with PyMuPDF: {file_path}")

        doc = await asyncio.to_thread(fitz.open, file_path)
        for page_number, page in enumerate(doc, start=1):
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if block['type'] == 0:  # Text block
                    text = "".join([line['text'] for line in block['lines']])
                    bbox = BoundingBox(
                        page=page_number,
                        bbox=coordinates(
                            left=block['bbox'][0],
                            top=block['bbox'][1],
                            width=block['bbox'][2] - block['bbox'][0],
                            height=block['bbox'][3] - block['bbox'][1]
                        ),
                        text=text.strip(),
                        confidence=100.0  # PyMuPDF does not provide confidence
                    )
                    text_and_boxes.append(bbox)
        doc.close()
        logger.info(f"PyMuPDF extracted {len(text_and_boxes)} bounding boxes")
        return PDFTextResponse(
            file_name=file_path,
            text="\n".join([bbox.text for bbox in text_and_boxes]),
            bounding_boxes=[bbox.dict() for bbox in text_and_boxes]
        ).to_dict()
    except Exception as e:
        logger.error(f"Failed to extract from PDF using PyMuPDF: {e}")
        return PDFTextResponse(file_name=file_path, text="", bounding_boxes=[]).to_dict()
