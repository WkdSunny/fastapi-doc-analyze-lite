"""
This module defines the AWS S3 file upload and download tasks.
It provides asynchronous functions to upload a file to an AWS S3 bucket and to download a file from an AWS S3 bucket.
"""

import uuid
import base64
from aiobotocore.session import AioSession
from botocore.exceptions import BotoCoreError
from fastapi import HTTPException
from app.config import settings, logger

async def upload_file_to_s3(file):
    """
    Uploads a file to an AWS S3 bucket.

    Parameters:
    - file: The file object to upload. The file object must have a 'name' attribute.

    Returns:
    - The temporary filename under which the file was uploaded in S3.

    Raises:
    - HTTPException: If the file upload fails due to BotoCoreError or any other exception.
    """
    try:
        # Generate a unique temporary filename
        temp_filename = f"{uuid.uuid4()}_{file.filename}"
        logger.info(f"Uploading file to S3: {file.filename} as {temp_filename}")  # Log the upload attempt
        session = AioSession()
        async with session.create_client('s3',
                                        region_name=settings.AWS_REGION,
                                        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY) as s3:
            logger.info(f"Uploading file: {file.filename} to S3 bucket: {settings.AWS_S3_BUCKET_NAME} as {temp_filename}")
            # Upload the file to S3
            await s3.put_object(Bucket=settings.AWS_S3_BUCKET_NAME, Key=temp_filename, Body=file.file)
            logger.info(f"File uploaded successfully to S3: {temp_filename}")  # Log successful upload
            return temp_filename
    except BotoCoreError as e:
        logger.error(f"Failed to upload file to S3: {e}")  # Log BotoCoreError
        raise HTTPException(status_code=500, detail="Failed to upload file to S3.")
    except Exception as e:
        logger.error(f"Unexpected error during file upload to S3: {e}")  # Log unexpected errors
        raise HTTPException(status_code=500, detail="Unexpected error during file upload to S3.")

async def download_file_from_s3(bucket_name, file_key):
    """
    Downloads a file from an AWS S3 bucket.

    Parameters:
    - bucket_name: The name of the S3 bucket.
    - file_key: The key of the file in the S3 bucket.

    Returns:
    - A BytesIO object containing the downloaded file data.

    Raises:
    - HTTPException: If the file download fails due to BotoCoreError or any other exception.
    """
    logger.info(f"Downloading file from S3: {file_key}")  # Log the download attempt
    session = AioSession()
    try:
        async with session.create_client('s3', region_name=settings.AWS_REGION,
                                        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY) as s3:
            try:
                response = await s3.get_object(Bucket=bucket_name, Key=file_key)
                async with response['Body'] as stream:
                    file_data = await stream.read()
                logger.info(f"File downloaded successfully from S3: {file_key}")  # Log successful download
                # Convert the binary data to a base64-encoded string
                # base64_encoded_data = base64.b64encode(file_data).decode('utf-8')
                # return base64_encoded_data
                return file_data
            except BotoCoreError as e:
                logger.error(f"Failed to download file from S3: {e}")  # Log BotoCoreError
                # raise HTTPException(status_code=500, detail="Failed to access file from S3.")
            except Exception as e:
                logger.error(f"Unexpected error during file download from S3: {e}")  # Log unexpected errors
                # raise HTTPException(status_code=500, detail="Unexpected error during file download from S3.")
    except BotoCoreError as e:
        logger.error(f"Failed to create client: {e}")
        # raise HTTPException(status_code=500, detail="Failed to create client for S3.")

# Example usage
# Note: These calls should be made within an async context
if __name__ == "__main__":
    import asyncio

    async def main():
        # Example call to upload a file to S3
        with open("path/to/your/file", "rb") as file:
            uploaded_filename = await upload_file_to_s3(file)

        # Example call to download a file from S3
        downloaded_file = await download_file_from_s3(settings.AWS_S3_BUCKET_NAME, uploaded_filename)
        with open("path/to/save/downloaded_file", "wb") as file:
            file.write(downloaded_file.getvalue())

    asyncio.run(main())
