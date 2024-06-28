from app.tasks.celery_config import app
import asyncio
import aiobotocore
from app.models.pdf_model import PDFTextResponse, BoundingBox
from app.config import settings, logger

@app.task
async def process_pdfs_with_textract(documents):
    """
    Process PDFs with AWS Textract.

    Args:
    documents (list): List of S3 document locations.

    Returns:
    list: List of PDFTextResponse objects.
    """
    try:
        async with aiobotocore.get_session().create_client('textract', region_name=settings.AWS_REGION) as client:
            job_ids = await submit_documents(client, documents)
            results = await get_results(client, job_ids)
            responses = [process_result(result) for result in results]
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
        return response['JobId']
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
        except Exception as e:
            logger.error(f"Failed to retrieve document text for Job ID {job_id}: {e}")
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
    return response

def process_result(result):
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
        return PDFTextResponse(file_name=result['DocumentLocation']['Name'], text=text, bounding_boxes=bounding_boxes)
    except Exception as e:
        logger.error(f"Failed to process result: {e}")
        return PDFTextResponse(file_name=result['DocumentLocation']['Name'], text="", bounding_boxes=[])

def extract_text(result):
    """
    Extract text from Textract result.

    Args:
    result (dict): Textract response.

    Returns:
    str: Extracted text.
    """
    try:
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
        return [
            BoundingBox(
                page=1,  # Assuming all text is from the first page
                bbox=[block['Geometry']['BoundingBox']['Left'], block['Geometry']['BoundingBox']['Top'],
                      block['Geometry']['BoundingBox']['Width'], block['Geometry']['BoundingBox']['Height']],
                text=block['Text']
            ) for block in result['Blocks'] if block['BlockType'] == 'LINE'
        ]
    except Exception as e:
        logger.error(f"Error extracting bounding boxes: {e}")
        return []
