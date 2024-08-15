# /src/app/routers/questions.py
"""
This module defines the RAG question generation routes for the FastAPI application.
"""

from fastapi import APIRouter, HTTPException
from app.services.rag.questions.hybrid_questions import IntegratedQuestionGeneration
from app.services.db.insert import insert_questions
from app.models.rag_model import RAGQuestionRequest
from app.config import logger

router = APIRouter(
    prefix="/questions",
    tags=["questions"]
)

@router.post("/")
async def get_questions(request: RAGQuestionRequest):
    """
    Generate questions for the given document.
    """
    question_generator = IntegratedQuestionGeneration()  # Initialize the question generator
    try:
        logger.debug(f"Received payload for question generation: {request.dict()}")

        # entities = request.entity_words
        # topics = request.topic_words

        # Extract the words from entities and topics for question generation
        # logger.debug(f"Entities: {entities}, Topics: {topics}")
        questions = await question_generator.generate_questions(document_text=request.document_text, document_id=request.document_id)
        question_generator.unload()
        # questions = question_generator.generate_questions(entities, topics)
        # question_generator.unload()

        # Add document_id to each question before inserting into the database
        # questions_with_id = [{"document_id": request.document_id, "question": q} for q in questions]

        # Insert questions into the database with the document_id
        # await insert_questions(questions_with_id)

        # return {"questions": questions_with_id}
        return questions

    except Exception as e:
        # question_generator.unload()
        logger.error(f"Error generating questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Commented out the simple example used for testing
# async def get_questions():
#     document_text = "This is a sample document text about Apple Inc. and its various products and services."

#     integrated_service = IntegratedQuestionGeneration()
#     questions = await integrated_service.generate_questions(document_text)

#     for question in questions:
#         print("Generated Question:", question)

#     return questions

    # return minimal_rag_example()
    # return t5_question_generation_example()