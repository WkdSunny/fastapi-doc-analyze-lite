import asyncio
from celery import shared_task
from app.services.processors.pdf import textract, tesseract, pdf_miner, pyPDF2, muPDF
from app.models.pdf_model import PDFTextResponse
from app.config import logger
import fitz  # PyMuPDF

def is_pdf_scanned(pdf_path):
    """
    Check if any page in a PDF is scanned.

    Args:
    pdf_path (str): The path to the PDF file.

    Returns:
    bool: True if any page is scanned, False otherwise.
    """
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            # Get the page's text to determine if it's mostly text-based
            text = page.get_text().strip()
            # Get the number of image blocks in the page
            img_blocks = page.get_images(full=True)
            
            # If there's very little text and at least one image, consider it scanned
            if len(text) < 50 and img_blocks:  # Threshold values can be adjusted
                return True
        return False
    except Exception as e:
        logger.error(f"Error determining if any page is scanned: {e}")
        return False  # Or handle the error as needed

@shared_task
async def process_pdf(file_path):
    """
    Process PDF files based on type and handle fallbacks.

    Args:
    file_path (str): The path to the PDF file.
    file_type (str): 'scanned' or 'readable' indicating the type of PDF.

    Returns:
    PDFTextResponse: Contains the file name, concatenated text, and bounding boxes.
    """
    try:
        scanned = is_pdf_scanned(file_path)
        if scanned:
            response = textract.useTextract(file_path)
            if not response.bounding_boxes:
                response = asyncio.run(tesseract.useTesseract(file_path))
        else:
            response = await asyncio.run(pdf_miner.usePDFMiner(file_path))
            if not response.bounding_boxes:
                response = asyncio.run(pyPDF2.usePyPDF2(file_path))
                if not response.bounding_boxes:
                    response = asyncio.run(muPDF.usePyMuPDF(file_path))
        return response
    except Exception as e:
        logger.error(f"Failed to process PDF {file_path} with error: {e}")
        return PDFTextResponse(file_name=file_path, text="", bounding_boxes=[])
