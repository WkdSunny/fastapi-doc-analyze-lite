from app.tasks.celery_config import app
from PyPDF2 import PdfReader
from app.models.pdf_model import PDFTextResponse, BoundingBox
from app.config import logger

@app.task
def extract_text_pypdf2(file_path):
    """
    Extracts text from a readable PDF using PyPDF2.
    Note: PyPDF2 does not provide bounding box information.

    Args:
    file_path (str): The path to the PDF file to be processed.

    Returns:
    PDFTextResponse: Contains the file name, concatenated text, and bounding boxes (None in this case).
    """
    try:
        text_and_boxes = []
        reader = PdfReader(file_path)
        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            # PyPDF2 does not provide bounding box information directly
            bbox = BoundingBox(
                page=page_number,
                bbox=None,
                text=text.strip()
            )
            text_and_boxes.append(bbox)
        return PDFTextResponse(file_name=file_path, text="\n".join([bbox.text for bbox in text_and_boxes]), bounding_boxes=text_and_boxes)
    except Exception as e:
        logger.error(f"Failed to extract from PDF using PyPDF2: {e}")
        return PDFTextResponse(file_name=file_path, text="", bounding_boxes=[])

# Example usage:
if __name__ == "__main__":
    path = "path_to_your_pdf_file.pdf"
    results = extract_text_pypdf2(path)
    print(results)
