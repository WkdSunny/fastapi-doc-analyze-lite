# /app/routers/convert.py
"""
This module defines the conversion routes for the FastAPI application.
"""

import asyncio
from typing import List, Dict, Any
from fastapi import APIRouter, File, UploadFile, HTTPException, Request
from app.config import settings, logger
from app.config import logger
from app.services.document_processors.pdf.textract import useTextract
from app.tasks.pdf_tasks import process_pdf
from app.tasks.excel_tasks import process_excel
from app.tasks.word_tasks import process_word
from app.tasks.img_tasks import process_img
from app.services.file_processing import save_temp_file, get_file_type, call_question_generation_api
# from app.services.document_classification import DocumentClassifier
# from app.services.entity_recognition import EntityRecognizer
# from app.services.document_segmentation import DocumentSegmenter
# from app.services.topic_modeling.pipeline import TopicModelingPipeline
# from app.services.tfidf_extraction import TFIDFExtractor
# from app.services.db.insert import insert_documents, insert_segments, insert_entities, insert_classification, insert_topics
from app.tasks.celery_tasks import wait_for_celery_task
# from app.models.rag_model import Segment, Entity, Topic, Classification

router = APIRouter(
    prefix="/convert",
    tags=["convert"]
)

# database = settings.database

@router.post("/", response_model=Dict[str, Any])
async def convert_files(request: Request, files: List[UploadFile] = File(...)):
    """
    Convert the uploaded files to text and process them for further analysis.

    Args:
        request (Request): The incoming request object.
        files (List[UploadFile]): The list of files to be processed.

    Returns:
        Dict[str, Any]: A dictionary containing the processing results.

    Raises:
        HTTPException: If there's an error during the file processing.
    """
    responses = []
    # segments_all: List[Segment] = []
    # entities_all: List[Entity] = []
    # topics_all: List[Topic] = []
    # classifications_all: List[Classification] = []

    # document_classifier = DocumentClassifier()
    # entity_recognizer = EntityRecognizer()
    # document_segmenter = DocumentSegmenter()
    # tfidf_extractor = TFIDFExtractor()

    for file in files:
        try:
            logger.info(f'Processing file: {file.filename}')
            content_type = await get_file_type(file)
            if content_type is None:
                raise ValueError("Cannot determine file type")
            logger.info(f"File type: {content_type}")

            # Save the file to a temporary path
            temp_path = await save_temp_file(file)
            logger.info(f"Saved file to temporary path: {temp_path}")

            # Process file based on type
            if 'pdf' in content_type:
                logger.info(f"PDF file detected...")
                task = process_pdf.delay(temp_path)
            elif 'excel' in content_type or 'spreadsheetml' in content_type:
                logger.info(f"Excel file detected...")
                task = process_excel.delay(temp_path)
            elif 'wordprocessingml' in content_type or 'msword' in content_type:
                logger.info(f"Word document detected...")
                task = process_word.delay(temp_path)
            elif 'image' in content_type:
                logger.info(f"Image file detected...")
                task = process_img.delay(temp_path)
            else:
                logger.error(f"Unsupported file type: {file.filename}")
                continue

            result = {
                "document_id": None,
                "classification": {},
            }
            result.update(await wait_for_celery_task(task.id, settings.PDF_PROCESSING_TIMEOUT))

            # # Prepare document data and segments
            # document_id = await insert_documents(file.filename, result["text"])
            # logger.info(f"Inserted document with ID: {document_id} into the database")

            # segments: List[Segment] = await document_segmenter.segment_document(result, content_type)
            # segments_all.extend(segments)

            # # Perform Entity Recognition on the extracted text
            # entities: List[Entity] = await entity_recognizer.recognize_entities(result["text"])
            # entities_all.extend(entities)

            # # Classify the document based on its content
            # classification: Classification = await document_classifier.classify_document(result["text"])
            # classifications_all.append({
            #     "document_id": document_id,
            #     "classification": classification
            # })
            # logger.info(f"Classified document with ID: {document_id} as {classification.label}")

            # doc_type = {
            #     "label": classification.label,
            #     "score": classification.score
            # }

            # result["document_id"] = document_id
            # result["classification"] = doc_type
            responses.append(result)

        except Exception as e:
            logger.error(f"Failed to process file {file.filename}: {e}")

    # After processing all files, insert data into the database
    # if segments_all:
    #     await insert_segments(document_id, segments_all)
    # # document_segmenter.unload()

    # if entities_all:
    #     await insert_entities(document_id, entities_all)
    #     logger.info(f"Inserted {len(entities_all)} entities for documents.")
    # entity_recognizer.unload()

    # for classification_data in classifications_all:
    #     await insert_classification(classification_data["document_id"], classification_data["classification"])
    #     logger.info(f"Classified document with ID: {classification_data['document_id']}")
    # document_classifier.unload()

    # # Example text documents extracted after processing
    # extracted_texts = [result["text"] for result in responses]
    # logger.info(f"Extracted texts: {extracted_texts}")

    # # Run topic modeling
    # topic_modeling_pipeline = TopicModelingPipeline(num_topics=5, passes=10)
    # topics_all = topic_modeling_pipeline.run(extracted_texts)

    # # Store topics in the database
    # for result in responses:
    #     document_id = result["document_id"]
    #     await insert_topics(document_id, topics_all)  # Insert topics for each document
    #     logger.info(f"Inserted topics for document ID: {document_id}")

    # 

    # Generate questions
    # entity_words = [entity.word for entity in entities_all]
    # topic_words = [word for topic in topics_all for word in topic.words]
    # logger.info(f"Entities from convert: {entity_words}, Topics from convert: {topic_words}")
    # await call_question_generation_api(
    #     request, 
    #     document_id, 
    #     entity_words, 
    #     topic_words
    # )
    # logger.info(f"Questions generated for document ID: {document_id}")

    if not responses:
        raise HTTPException(status_code=500, detail="No files processed successfully")

    return {
        "status": 200,
        "success": True,
        "result": responses
    }

if __name__ == "__main__":
    files = [
        UploadFile(filename="sample.pdf", content_type="application/pdf"),
        UploadFile(filename="sample.xlsx", content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        UploadFile(filename="sample.docx", content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        UploadFile(filename="sample.jpg", content_type="image/jpeg"),
        UploadFile(filename="sample.txt", content_type="text/plain")
    ]
    results = asyncio.run(convert_files(files))
    print(results)
