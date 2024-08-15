# # convert_v1.py
# """
# This module defines the conversion routes for the FastAPI application.
# """

# import torch
# import asyncio
# import aiofiles
# import filetype
# from typing import List, Dict, Any
# from datetime import datetime, timezone
# from transformers import pipeline
# from transformers import BertTokenizer, BertForTokenClassification, BertForSequenceClassification
# from fastapi import APIRouter, File, UploadFile, HTTPException
# from concurrent.futures import ThreadPoolExecutor
# from app.config import settings, logger
# from app.services.processors.word import useDocX
# from app.services.processors.excel import useOpenPyXL
# from app.services.file_processing import save_temp_file, get_file_type
# from app.services.document_classification import classify_document
# from app.services.entity_recognition import recognize_entities
# from app.utils.celery_utils import wait_for_celery_task
# from app.services.processors.pdf.textract import useTextract
# from app.services.processors.pdf.pdf_tasks import process_pdf

# router = APIRouter(
#     prefix="/convert_v1",
#     tags=["convert"]
# )

# database = settings.database

# @router.post("/", response_model=Dict[str, Any])
# async def convert_files(files: List[UploadFile] = File(...)):
#     responses = []

#     for file in files:
#         try:
#             logger.info(f'Processing file: {file.filename}')
#             content_type = await get_file_type(file)
#             if content_type is None:
#                 raise ValueError("Cannot determine file type")
#             logger.info(f"File type: {content_type}")

#             # Save the file to a temporary path
#             temp_path = await save_temp_file(file)
#             logger.info(f"Saved file to temporary path: {temp_path}")

#             # Process file based on type
#             if 'pdf' in content_type:
#                 logger.info(f"PDF file detected...")
#                 task = process_pdf.delay(temp_path)
#             elif 'excel' in content_type or 'spreadsheetml' in content_type:
#                 task = useOpenPyXL.delay(temp_path)
#             elif 'wordprocessingml' in content_type or 'msword' in content_type:
#                 task = useDocX.delay(temp_path)
#             elif 'image' in content_type:
#                 task = useTextract.delay(temp_path)
#             else:
#                 # unsupported_files.append(file.filename)
#                 logger.error(f"Unsupported file type: {file.filename}")
#                 continue
            
#             result = {
#                 "document_id": None,
#                 "classification": {},
#             }
#             result.update(await wait_for_celery_task(task.id, settings.PDF_PROCESSING_TIMEOUT))

#             # Prepare document data and segments
#             document_data = {
#                 "file_name": file.filename,
#                 "uploaded_at": datetime.now(timezone.utc),
#                 "text": result["text"],  # Extracted text
#                 "status": "processed"
#             }

#             segments = [
#                 {
#                     "page": bbox["page"],
#                     "bbox": {
#                         "left": float(bbox["bbox"]["left"]),
#                         "top": float(bbox["bbox"]["top"]),
#                         "width": float(bbox["bbox"]["width"]),
#                         "height": float(bbox["bbox"]["height"]),
#                     },
#                     "text": bbox["text"],
#                     "confidence": float(bbox["confidence"])  # Convert to regular float
#                 }
#                 for bbox in result["bounding_boxes"]
#             ]

#             # Insert data into MongoDB
#             document_id = await insert_documents(document_data, segments)
#             logger.info(f"Inserted document with ID: {document_id} into the database")

#             # Perform Entity Recognition on the extracted text
#             entities = await recognize_entities(result["text"])
#             # Store the entities
#             for entity in entities:
#                 entity_record = {
#                     "document_id": document_id,
#                     "word": entity["word"],
#                     "entity": entity["entity"],
#                     "score": float(entity["score"]),  # Convert to regular float
#                     "start": entity["start"],
#                     "end": entity["end"]
#                 }
#                 database["Entities"].insert_one(entity_record)

#             # Classify the document based on its content
#             classification = await classify_document(result["text"])
#             classification_record = {
#                 "document_id": document_id,
#                 "label": classification["label"],
#                 "score": float(classification["score"])  # Convert to regular float
#             }
#             database["DocumentClassification"].insert_one(classification_record)
#             logger.info(f"Classified document with ID: {document_id} as {classification['label']}")

#             doc_type = {
#                 "label": classification["label"],
#                 "score": classification["score"]
#             }

#             result["document_id"] = document_id
#             result["classification"] = doc_type
#             responses.append(result)
#         except Exception as e:
#             # failed_files.append(file.filename)
#             logger.error(f"Failed to process file {file.filename}: {e}")

#     if not responses:
#         raise HTTPException(status_code=500, detail="No files processed successfully")

#     return {
#         "status": 200,
#         "success": True,
#         # "unsupported_files": unsupported_files,
#         # "conversion_failed": failed_files,
#         "result": responses
#     }

# # Example usage:
# if __name__ == "__main__":
#     files = [
#         UploadFile(filename="sample.pdf", content_type="application/pdf"),
#         UploadFile(filename="sample.xlsx", content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
#         UploadFile(filename="sample.docx", content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
#         UploadFile(filename="sample.jpg", content_type="image/jpeg"),
#         UploadFile(filename="sample.txt", content_type="text/plain")
#     ]
#     results = asyncio.run(convert_files(files))
#     print(results)