# app/services/processors/pdf/pdf_miner.py

import asyncio
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
from app.tasks.celery_config import app
from app.models.pdf_model import PDFTextResponse, BoundingBox, coordinates
from app.tasks.async_tasks import run_async_task
from app.config import logger

# @app.task(bind=True, max_retries=3, default_retry_delay=5)
@app.task()
def usePDFMiner(self, file_path):
    """
    Extracts text and bounding boxes from a readable PDF using PDFMiner.
    """
    try:
        return run_async_task(_usePDFMiner, file_path)
    except Exception as e:
        logger.error(f"Failed to extract from PDF using PDFMiner: {e}")
        raise self.retry(exc=e)

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
        pages = await asyncio.to_thread(extract_pages, file_path)
        for page_number, page_layout in enumerate(pages, start=1):
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    text = await asyncio.to_thread(element.get_text)
                    bbox = BoundingBox(
                        page=page_number,
                        bbox=coordinates(
                            left=element.bbox[0],
                            top=element.bbox[1],
                            width=element.bbox[2] - element.bbox[0],
                            height=element.bbox[3] - element.bbox[1]
                        ),
                        text=text.strip(),
                        confidence=100.0  # PDFMiner does not provide confidence
                    )
                    text_and_boxes.append(bbox)
        logger.info(f"PDFMiner extracted {len(text_and_boxes)} bounding boxes")
        return PDFTextResponse(
            file_name=file_path,
            text="\n".join([bbox.text for bbox in text_and_boxes]),
            bounding_boxes=[bbox.dict() for bbox in text_and_boxes]
        ).to_dict()
    except Exception as e:
        logger.error(f"Failed to extract from PDF using PDFMiner: {e}")
        return PDFTextResponse(file_name=file_path, text="", bounding_boxes=[]).to_dict()
