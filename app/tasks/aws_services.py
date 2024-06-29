# aws_services.py
"""
This module defines the AWS S3 file upload and download tasks.
"""

import io
import uuid
import aiobotocore
from botocore.exceptions import BotoCoreError
from fastapi import HTTPException
from app.config import settings, logger

async def upload_file_to_s3(file, filename):
    temp_filename = f"{uuid.uuid4()}_{filename}"
    session = aiobotocore.get_session()
    try:
        async with session.create_client('s3', region_name=settings.AWS_REGION, 
                                         aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                         aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY) as s3:
            await s3.upload_fileobj(file, settings.AWS_S3_BUCKET_NAME, temp_filename)
        return temp_filename
    except BotoCoreError as e:
        logger.error(f"Failed to upload file to S3: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload file to S3.")
    except Exception as e:
        logger.error(f"Unexpected error during file upload to S3: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error during file upload to S3.")

async def download_file_from_s3(bucket_name, file_key):
    session = aiobotocore.get_session()
    async with session.create_client('s3', region_name=settings.AWS_REGION, 
                                     aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                     aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY) as s3:
        try:
            response = await s3.get_object(Bucket=bucket_name, Key=file_key)
            async with response['Body'] as stream:
                file_data = await stream.read()
                return io.BytesIO(file_data)
        except BotoCoreError as e:
            logger.error(f"Failed to download file from S3: {e}")
            raise HTTPException(status_code=500, detail="Failed to access file from S3.")
        except Exception as e:
            logger.error(f"Unexpected error during file download from S3: {e}")
            raise HTTPException(status_code=500, detail="Unexpected error during file download from S3.")
