# /app/services/processors/pdf/textract.py
"""
This module defines the PDF processing task using AWS Textract.
"""

import asyncio
from aiobotocore.session import AioSession
from app.tasks.celery_config import app
from app.models.pdf_model import PDFTextResponse, BoundingBox, coordinates
from app.config import settings, logger
from app.tasks.async_tasks import run_async_task
from app.tasks.aws_services import upload_file_to_s3

# @app.task(bind=True, max_retries=3, default_retry_delay=5)
@app.task()
def useTextract(self, file_path):
    """
    Process PDFs with AWS Textract.

    Args:
    file_path (str): The path to the PDF file.

    Returns:
    dict: PDFTextResponse containing the file name, concatenated text, and bounding boxes.
    """
    try:
        result = run_async_task(_useTextract, file_path)
        return result
    except Exception as e:
        logger.error(f"Failed to process PDFs with Textract: {e}")
        # Retry logic for large files or temporary issues
        raise self.retry(exc=e)

async def _useTextract(file_path):
    """
    Process PDFs with AWS Textract asynchronously.

    Args:
    file_path (str): The path to the PDF file.

    Returns:
    dict: PDFTextResponse containing the file name, concatenated text, and bounding boxes.
    """
    try:
        logger.info("Processing PDFs with Textract")

        # Upload file to S3
        s3_file_key = await upload_file_to_s3(file_path)
        logger.info(f"Uploaded file to S3 with key: {s3_file_key}")

        # Prepare the document reference for Textract
        document = {'Bucket': settings.AWS_S3_BUCKET_NAME, 'Name': s3_file_key}

        session = AioSession()
        async with session.create_client('textract', region_name=settings.AWS_REGION,
                                         aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                         aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY) as client:
            logger.info(f"Submitting document to Textract: {document}")
            job_id = await submit_document(client, document)
            logger.info(f"Submitted document to Textract, job ID: {job_id}")
            result = await get_result(client, job_id)
            logger.info(f"Retrieved result from Textract for job ID: {job_id}")
            response = process_result(result, document['Name'])
            logger.info("Processed all PDFs with Textract")
            return response
    except Exception as e:
        logger.error(f"Failed to process PDFs with Textract: {e}")
        return PDFTextResponse(file_name=file_path, text="", bounding_boxes=[]).to_dict()

async def submit_document(client, document):
    """
    Submit a document for text detection to AWS Textract.

    Args:
    client (obj): The Textract client.
    document (dict): S3 document location.

    Returns:
    str: Job ID.
    """
    try:
        response = await client.start_document_text_detection(DocumentLocation={'S3Object': document})
        logger.info(f"Started text detection for document: {document['Name']}, Job ID: {response['JobId']}")
        return response['JobId']
    except KeyError as e:
        logger.error(f"DocumentLocation missing in Textract result: {e}")
        raise
    except Exception as e:
        logger.error(f"Error starting text detection: {e}")
        raise

async def get_result(client, job_id):
    """
    Get results of document text detection.

    Args:
    client (obj): The Textract client.
    job_id (str): The job ID.

    Returns:
    dict: Textract response.
    """
    try:
        attempts = 0
        while True:
            response = await client.get_document_text_detection(JobId=job_id)
            logger.info(f"Job Status for {job_id}: {response['JobStatus']}")
            if response['JobStatus'] in ['SUCCEEDED', 'FAILED']:
                break
            attempts += 1
            if attempts > 5:
                logger.warning(f"Too many attempts for Job ID {job_id}. Increasing wait time.")
                await asyncio.sleep(10)
            else:
                await asyncio.sleep(5)
        logger.info(f"Retrieved document text detection result for Job ID {job_id}")
        return response
    except Exception as e:
        logger.error(f"Failed to retrieve document text for Job ID {job_id}: {e}")
        raise

def process_result(result, doc_name):
    """
    Process Textract result.

    Args:
    result (dict): Textract response.
    doc_name (str): Document name.

    Returns:
    dict: PDFTextResponse containing the file name, concatenated text, and bounding boxes.
    """
    try:
        text = extract_text(result)
        bounding_boxes = extract_bounding_boxes(result)
        cleaned_filename = '_'.join(doc_name.split('_')[1:])
        logger.info(f"Processed Textract result for document: {cleaned_filename}")
        return PDFTextResponse(file_name=cleaned_filename, text=text, bounding_boxes=bounding_boxes).to_dict()
    except Exception as e:
        logger.error(f"Failed to process result: {e}")
        return PDFTextResponse(file_name=doc_name, text="", bounding_boxes=[]).to_dict()

def extract_text(result):
    """
    Extract text from Textract result.

    Args:
    result (dict): Textract response.

    Returns:
    str: Extracted text.
    """
    try:
        logger.info("Extracting text from Textract result")
        return '\n'.join(block['Text'] for block in result['Blocks'] if block['BlockType'] == 'LINE')
    except Exception as e:
        logger.error(f"Error extracting text: {e}")
        return ""

def extract_bounding_boxes(result):
    """
    Extract bounding boxes from Textract result.

    Args:
    result (dict): Textract response.

    Returns:
    list: List of BoundingBox objects.
    """
    try:
        logger.info("Extracting bounding boxes from Textract result")
        return [
            BoundingBox(
                page=block['Page'] if 'Page' in block else 1,
                bbox=coordinates(
                    left=block['Geometry']['BoundingBox']['Left'],
                    top=block['Geometry']['BoundingBox']['Top'],
                    width=block['Geometry']['BoundingBox']['Width'],
                    height=block['Geometry']['BoundingBox']['Height']
                ),
                text=block['Text'],
                confidence=block['Confidence']
            ) for block in result['Blocks'] if block['BlockType'] == 'LINE'
        ]
    except Exception as e:
        logger.error(f"Error extracting bounding boxes: {e}")
        return []

# Example usage:
if __name__ == "__main__":
    file_path = '/tmp/sample.pdf'
    results = asyncio.run(_useTextract(file_path))
    print(results)
