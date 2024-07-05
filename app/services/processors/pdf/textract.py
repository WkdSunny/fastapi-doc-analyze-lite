# textract.py
"""
This module defines the PDF processing task using AWS Textract.
"""

from celery import shared_task
import asyncio
from aiobotocore.session import AioSession
from app.models.pdf_model import PDFTextResponse, BoundingBox, coordinates
from app.config import settings, logger
from app.utils.async_utils import run_async_task
from app.tasks.aws_services import upload_file_to_s3

@shared_task
def useTextract(file_path):
    """
    Process PDFs with AWS Textract.

    Args:
    file_path (str): The path to the PDF file.

    Returns:
    list: List of PDFTextResponse objects.
    """
    try:
        results = run_async_task(_useTextract, file_path)
        return results
    except Exception as e:
        logger.error(f"Failed to process PDFs with Textract: {e}")
        return PDFTextResponse(file_name=file_path, text="", bounding_boxes=[]).to_dict()

async def _useTextract(file_path):
    """
    Process PDFs with AWS Textract.

    Args:
    file_path (str): The path to the PDF file.

    Returns:
    list: List of PDFTextResponse objects.
    """
    try:
        logger.info("Processing PDFs with Textract")
        
        # Upload file to S3
        s3_file_key = await upload_file_to_s3(file_path)
        logger.info(f"Uploaded file to S3 with key: {s3_file_key}")
        
        # Prepare the document reference for Textract
        documents = [{'Bucket': settings.AWS_S3_BUCKET_NAME, 'Name': s3_file_key}]
        
        session = AioSession()
        async with session.create_client('textract', region_name=settings.AWS_REGION,
                                         aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                         aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY) as client:
            job_ids = await submit_documents(client, documents)
            results = await get_results(client, job_ids)
            responses = [process_result(result, doc['Name']) for result, doc in zip(results, documents)]
            logger.info("Processed all PDFs with Textract")
            return responses
    except Exception as e:
        logger.error(f"Failed to process PDFs with Textract: {e}")
        return []

async def submit_documents(client, documents):
    """
    Submit documents for text detection to AWS Textract.

    Args:
    client (obj): The Textract client.
    documents (list): List of S3 document locations.

    Returns:
    list: List of job IDs.
    """
    try:
        tasks = [process_document(client, doc) for doc in documents]
        logger.info("Submitting documents for text detection")
        return await asyncio.gather(*tasks)
    except Exception as e:
        logger.error(f"Error submitting documents for text detection: {e}")
        raise

async def process_document(client, document):
    """
    Start document text detection.

    Args:
    client (obj): The Textract client.
    document (dict): S3 document location.

    Returns:
    str: Job ID.
    """
    try:
        response = await client.start_document_text_detection(DocumentLocation={'S3Object': document})
        logger.info(f"Started text detection for document: {document['Name']}")
        return response['JobId']
    except KeyError as e:
        logger.error(f"DocumentLocation missing in Textract result: {e}")
        raise
    except Exception as e:
        logger.error(f"Error starting text detection: {e}")
        raise

async def get_results(client, job_ids):
    """
    Get results of document text detection.

    Args:
    client (obj): The Textract client.
    job_ids (list): List of job IDs.

    Returns:
    list: List of Textract responses.
    """
    try:
        tasks = [get_document_text(client, job_id) for job_id in job_ids]
        results = await asyncio.gather(*tasks)
        logger.info("Retrieved all document text detection results")
        return results
    except Exception as e:
        logger.error(f"Error retrieving document text detection results: {e}")
        raise

async def get_document_text(client, job_id):
    """
    Get document text detection result.

    Args:
    client (obj): The Textract client.
    job_id (str): The job ID.

    Returns:
    dict: Textract response.
    """
    try:
        while True:
            response = await client.get_document_text_detection(JobId=job_id)
            if response['JobStatus'] in ['SUCCEEDED', 'FAILED']:
                break
            await asyncio.sleep(5)  # Reduce frequency of checks to avoid rate limits
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
    PDFTextResponse: Processed result.
    """
    try:
        text = extract_text(result)
        bounding_boxes = extract_bounding_boxes(result)
        cleaned_filename = '_'.join(doc_name.split('_')[1:])
        logger.info("Processed Textract result")
        return PDFTextResponse(file_name=cleaned_filename, text=text, bounding_boxes=bounding_boxes).to_dict()
    except Exception as e:
        logger.error(f"Failed to process result: {e}")
        return PDFTextResponse(file_name=cleaned_filename, text="", bounding_boxes=[]).to_dict()

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
    results = asyncio.run(useTextract(file_path))
    print(results)
