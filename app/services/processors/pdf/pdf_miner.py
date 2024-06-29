from app.tasks.celery_config import app
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
from app.models.pdf_model import BoundingBox, PDFTextResponse
from app.config import logger
import asyncio

@app.task
async def usePDFMiner(file_path):
    """
    Asynchronously extracts text and bounding boxes from a readable PDF using PDFMiner.six.
    Each text block's bounding box and text content are stored.

    Args:
    file_path (str): The path to the PDF file to be processed.

    Returns:
    PDFTextResponse: Contains the file name, concatenated text, and bounding boxes.
    """
    try:
        text_and_boxes = []
        # Run extract_pages in a separate thread
        pages = await asyncio.to_thread(extract_pages, file_path)
        for page_number, page_layout in enumerate(pages, start=1):
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    # Run element.get_text() in a separate thread
                    text = await asyncio.to_thread(element.get_text)
                    bbox = BoundingBox(
                        page=page_number,
                        bbox=[int(coord) for coord in element.bbox],
                        text=text.strip()
                    )
                    text_and_boxes.append(bbox)
        return PDFTextResponse(file_name=file_path, text="\n".join([bbox.text for bbox in text_and_boxes]), bounding_boxes=text_and_boxes)
    except Exception as e:
        logger.error(f"Failed to extract from PDF using PDFMiner: {e}")
        return PDFTextResponse(file_name=file_path, text="", bounding_boxes=[])

# Example usage:
if __name__ == "__main__":
    path = "path_to_your_pdf_file.pdf"
    # Use asyncio.run to execute the async function
    results = asyncio.run(usePDFMiner(path))
    print(results)
