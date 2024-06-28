from app.tasks.celery_config import app
import fitz  # PyMuPDF
from app.models.pdf_model import BoundingBox, PDFTextResponse
from app.config import logger

@app.task
def extract_text_and_boxes_pymupdf(file_path):
    """
    Extracts text and bounding boxes from a readable PDF using PyMuPDF (MuPDF).
    Each text block's bounding box and text content are stored.

    Args:
    file_path (str): The path to the PDF file to be processed.

    Returns:
    PDFTextResponse: Contains the file name, concatenated text, and bounding boxes.
    """
    try:
        text_and_boxes = []
        doc = fitz.open(file_path)
        for page_number, page in enumerate(doc, start=1):
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if block['type'] == 0:  # Text block
                    text = "".join([line['text'] for line in block['lines']])
                    bbox = BoundingBox(
                        page=page_number,
                        bbox=[int(coord) for coord in block['bbox']],
                        text=text.strip()
                    )
                    text_and_boxes.append(bbox)
        doc.close()
        return PDFTextResponse(file_name=file_path, text="\n".join([bbox.text for bbox in text_and_boxes]), bounding_boxes=text_and_boxes)
    except Exception as e:
        logger.error(f"Failed to extract from PDF using PyMuPDF: {e}")
        return PDFTextResponse(file_name=file_path, text="", bounding_boxes=[])

# Example usage:
if __name__ == "__main__":
    path = "path_to_your_pdf_file.pdf"
    results = extract_text_and_boxes_pymupdf(path)
    print(results)
