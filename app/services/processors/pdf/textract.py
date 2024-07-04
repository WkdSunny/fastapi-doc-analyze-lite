# textract.py
"""
This module defines the PDF processing task using AWS Textract.
"""

from app.tasks.celery_config import app
import asyncio
from aiobotocore.session import AioSession
from app.models.pdf_model import PDFTextResponse, BoundingBox, coordinates
from app.models.pdf_model import BoundingBox
from app.config import settings, logger

@app.task
def useTextract(documents):
    """
    Process PDFs with AWS Textract.

    Args:
    documents (list): List of S3 document locations.

    Returns:
    list: List of PDFTextResponse objects.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(_useTextract(documents), loop)
            return future.result()
        else:
            return loop.run_until_complete(_useTextract(documents))
    except Exception as e:
        logger.error(f"Failed to process PDFs with Textract: {e}")
        return []  # Return empty list or handle as needed
    
async def _useTextract(documents):
    """
    Process PDFs with AWS Textract.

    Args:
    documents (list): List of S3 document locations.

    Returns:
    list: List of PDFTextResponse objects.
    """
    try:
        session = AioSession()
        logger.info("Processing PDFs with Textract")
        logger.info(f"Creating Textract client from region: {settings.AWS_REGION}")
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
        return []  # Return empty list or handle as needed

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
    results = []
    for job_id in job_ids:
        try:
            results.append(await get_document_text(client, job_id))
            logger.info(f"Retrieved document text for Job ID {job_id}")
        except Exception as e:
            logger.error(f"Failed to retrieve document text for Job ID {job_id}: {e}")
    logger.info("Retrieved all document text detection results")
    return results

async def get_document_text(client, job_id):
    """
    Get document text detection result.

    Args:
    client (obj): The Textract client.
    job_id (str): The job ID.

    Returns:
    dict: Textract response.
    """
    while True:
        response = await client.get_document_text_detection(JobId=job_id)
        if response['JobStatus'] in ['SUCCEEDED', 'FAILED']:
            break
        await asyncio.sleep(5)  # Reduce frequency of checks to avoid rate limits
    logger.info(f"Retrieved document text detection result for Job ID {job_id}")
    return response

def process_result(result, docName):
    """
    Process Textract result.

    Args:
    result (dict): Textract response.

    Returns:
    PDFTextResponse: Processed result.
    """
    try:
        text = extract_text(result)
        bounding_boxes = extract_bounding_boxes(result)
        cleaned_filename = '_'.join(docName.split('_')[1:])
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
                page = block['Page'] if 'Page' in block else 1,
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
    documents = [{'Bucket': 'your-bucket-name', 'Name': 'your-document-name.pdf'}]
    results = asyncio.run(useTextract(documents))
    print(results)
