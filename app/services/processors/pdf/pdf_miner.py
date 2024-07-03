import asyncio
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
from app.tasks.celery_config import app
# from app.models.pdf_model import BoundingBox, PDFTextResponse
from app.models.pdf_model import BoundingBox
from app.config import logger

@app.task
def process_pdfminer_tasks(file_path):
    """
    Process a PDF file to extract text and bounding boxes using PDFMiner.

    Args:
    file_path (str): The path to the PDF file to be processed.

    Returns:
    dict: Contains the file name, concatenated text, and bounding boxes.
    """
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # If the loop is already running, you might need to run your coroutine differently,
        # for example, using run_coroutine_threadsafe or ensuring it's called from an async context.
        future = asyncio.run_coroutine_threadsafe(usePDFMiner(file_path), loop)
        return future.result()
    else:
        # If the loop is not running, you can just call your coroutine.
        return loop.run_until_complete(usePDFMiner(file_path))

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
                        bbox=[int(coord) for coord in element.bbox],
                        text=text.strip()
                    )
                    text_and_boxes.append(bbox)
        logger.info(f"Extracted text from PDF using PDFMiner: {file_path}")
        # return PDFTextResponse(file_name=file_path, text="\n".join([bbox.text for bbox in text_and_boxes]), bounding_boxes=text_and_boxes).to_dict()
        return {
            "file_name": file_path,
            "text": "\n".join([bbox.text for bbox in text_and_boxes]),
            "bounding_boxes": text_and_boxes
        }
        # logger.info(f"Returning PDFMiner response: {response}")
        # return response.to_dict()
    except Exception as e:
        logger.error(f"Failed to extract from PDF using PDFMiner: {e}")
        # return PDFTextResponse(file_name=file_path, text="", bounding_boxes=[]).to_dict
        return {
            "file_name": file_path,
            "text": "",
            "bounding_boxes": []
        }

# Example usage:
if __name__ == "__main__":
    path = "path_to_your_pdf_file.pdf"
    # Use asyncio.run to execute the async function
    results = asyncio.run(usePDFMiner(path))
    print(results)
