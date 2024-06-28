from celery import shared_task
from app.services.processors.pdf import textract, tesseract, pdf_miner, pypdf2, mupdf
from app.models.pdf_model import PDFTextResponse
from app.config import logger

@shared_task
def process_pdf(file_path, file_type):
    """
    Process PDF files based on type and handle fallbacks.

    Args:
    file_path (str): The path to the PDF file.
    file_type (str): 'scanned' or 'readable' indicating the type of PDF.

    Returns:
    PDFTextResponse: Contains the file name, concatenated text, and bounding boxes.
    """
    try:
        if file_type == 'scanned':
            response = textract.process_pdfs_with_textract(file_path)
            if not response.bounding_boxes:
                response = tesseract.use_tesseract(file_path)
        elif file_type == 'readable':
            response = pdf_miner.extract_text_and_boxes_pdfminer(file_path)
            if not response.bounding_boxes:
                response = pypdf2.extract_text_pypdf2(file_path)
                if not response.bounding_boxes:
                    response = mupdf.extract_text_and_boxes_pymupdf(file_path)
        return response
    except Exception as e:
        logger.error(f"Failed to process PDF {file_path} with error: {e}")
        return PDFTextResponse(file_name=file_path, text="", bounding_boxes=[])
