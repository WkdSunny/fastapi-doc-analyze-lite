# tesseract.py
"""
This module defines the Tesseract OCR processing task for PDF files.
"""

from app.tasks.celery_config import app
import asyncio
import numpy as np
import cv2
from PIL import Image
from skimage.transform import rotate
from skimage.measure import label, regionprops
from pdf2image import convert_from_path, exceptions as pdf_exceptions
import pytesseract
from app.config import logger
from app.models.pdf_model import BoundingBox, PDFTextResponse

async def deskew(image):
    """Deskew the given image based on text orientation."""
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        label_img = label(binary)
        regions = regionprops(label_img)
        angle = regions[0].orientation * 180 / np.pi
        skew_angle = angle if angle < 90 else angle - 180
        deskewed = rotate(image, skew_angle, resize=True)
        return cv2.convertScaleAbs(deskewed, alpha=(255.0))
    except Exception as e:
        logger.error(f"Failed to deskew image: {e}")
        return image  # Return original image if deskewing fails

async def process_image(image):
    """Convert and preprocess image for OCR."""
    try:
        deskewed = await deskew(np.array(image))
        gray = cv2.cvtColor(deskewed, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        resized = cv2.resize(thresh, None, fx=1, fy=1, interpolation=cv2.INTER_CUBIC)
        kernel = np.ones((1, 1), np.uint8)
        processed_img = cv2.dilate(resized, kernel, iterations=1)
        processed_img = cv2.erode(processed_img, kernel, iterations=1)
        return Image.fromarray(processed_img)
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        return None  # Return None if processing fails

async def extract_text_and_boxes(image):
    """Extract text and bounding boxes using pytesseract from the processed image."""
    if image is None:
        return []
    try:
        ocr_data = pytesseract.image_to_data(image, config='--oem 3 --psm 6', output_type=pytesseract.Output.DICT)
        text_and_boxes = [
            BoundingBox(
                page=int(ocr_data['page_num'][i]),
                bbox=[ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i]],
                text=ocr_data['text'][i].strip()
            ) for i in range(len(ocr_data['text'])) if int(ocr_data['conf'][i]) > 60 and ocr_data['text'][i].strip()
        ]
        return text_and_boxes
    except Exception as e:
        logger.error(f"Failed to extract text and bounding boxes: {e}")
        return []

@app.task
async def useTesseract(file_path):
    """
    Process a PDF file to extract text using OCR.

    Args:
    file_path (str): The path to the PDF file to be processed.

    Returns:
    PDFTextResponse: Contains the file name, concatenated text, and bounding boxes.
    """
    try:
        images = convert_from_path(file_path, dpi=300, fmt='jpeg')
    except pdf_exceptions.PDFInfoNotInstalledError as e:
        logger.error(f"PDFInfo not installed, cannot convert PDF: {e}")
        return PDFTextResponse(file_name=file_path, text="", bounding_boxes=[])
    except pdf_exceptions.PDFPageCountError as e:
        logger.error(f"Cannot read page count: {e}")
        return PDFTextResponse(file_name=file_path, text="", bounding_boxes=[])
    except Exception as e:
        logger.error(f"Failed to convert PDF to image: {e}")
        return PDFTextResponse(file_name=file_path, text="", bounding_boxes=[])

    tasks = [process_image(image) for image in images]
    processed_images = await asyncio.gather(*tasks)
    results = await asyncio.gather(*(extract_text_and_boxes(image) for image in processed_images))
    text_responses = PDFTextResponse(file_name=file_path, text="\n".join([box.text for result in results for box in result]), bounding_boxes=[box for result in results for box in result])
    return text_responses

# Example usage:
if __name__ == "__main__":
    file_path = 'path_to_your_pdf_file.pdf'
    results = asyncio.run(useTesseract(file_path))
    print(results)
