# /app/services/rag/questions/hybrid_questions.py
"""
This module defines the integrated question generation service for the FastAPI application.
"""

from typing import List, Optional
from app.services.entity_recognition import EntityRecognizer
from app.services.tfidf_extraction import TFIDFExtractor
from app.services.topic_modeling.pipeline import TopicModelingPipeline
from app.services.rag.questions.gpt4_question_generator import GPT4QuestionGenerator
from app.services.rag.questions.question_evaluation_model import QuestionEvaluator 
from app.services.db.insert import insert_entities, insert_topics, insert_questions, insert_tf_idf_keywords
from app.config import settings

class IntegratedQuestionGeneration:
    """
    A service class for generating questions based on entities, topics, and TF-IDF keywords using GPT-4.

    Attributes:
        entity_recognizer (EntityRecognizer): An instance of the EntityRecognizer class.
        topic_modeling_pipeline (TopicModelingPipeline): An instance of the TopicModelingPipeline class.
        tfidf_extractor (TFIDFExtractor): An instance of the TFIDFExtractor class.
        question_generator (GPT4QuestionGenerator): An instance of the GPT4QuestionGenerator class.
    """
    def __init__(self):
        self.entity_recognizer = EntityRecognizer()
        self.topic_modeling_pipeline = TopicModelingPipeline(num_topics=5, passes=10)
        self.tfidf_extractor = TFIDFExtractor()
        self.question_generator = GPT4QuestionGenerator(api_key=settings.OPENAI_API_KEY)
        self.question_evaluator = QuestionEvaluator()

    async def generate_questions(self, document_text: str, document_id: Optional[str]) -> List[str]:
        """
        Integrates entities, topics, and TF-IDF keywords to generate questions.

        Args:
            document_text (str): The text of the document.

        Returns:
            List[str]: A list of generated questions.
        """
        try:
            # Step 1: Extract Entities (Await the asynchronous call)
            entities = await self.entity_recognizer.recognize_entities(document_text)
            if not entities:
                raise ValueError("No entities found in the document.")
            await insert_entities(document_id, entities)

            # Step 2: Extract Topics
            topics = self.topic_modeling_pipeline.run([document_text])
            if not topics:
                raise ValueError("No topics found in the document.")
            await insert_topics(document_id, topics)

            # Step 3: Extract TF-IDF Keywords
            tfidf_keywords = await self.tfidf_extractor.extract_keywords(document_text)
            if not tfidf_keywords:
                raise ValueError("No TF-IDF keywords found in the document.")
            await insert_tf_idf_keywords(document_id, tfidf_keywords)

            # Step 4: Combine Entities, Topics, and TF-IDF Keywords
            combined_keywords = list(set([entity.word for entity in entities] +
                                        [word for topic in topics for word in topic.words] +
                                        tfidf_keywords))

            # Step 5: Generate Questions using GPT-4 (Await the asynchronous call)
            questions = await self.question_generator.generate_questions(combined_keywords)
            if not questions:
                raise ValueError("No questions generated.")

            # Step 6: Evaluate Questions to assign confidence scores
            questions_with_scores = []
            for question in questions:
                added_confidence_score = await self.question_evaluator.combined_evaluation(question)
                questions_with_scores.append(added_confidence_score)

            # Insert the questions into the database
            await insert_questions(document_id, questions_with_scores, combined_keywords)
            return questions_with_scores
        except Exception as e:
            raise RuntimeError(f"Error generating questions: {e}")
        
    def unload(self):
        """
        Unload the resources used by the integrated question generation service.
        """
        self.entity_recognizer.unload()
        # self.topic_modeling_pipeline.unload()
        # self.tfidf_extractor.unload()
        # self.question_generator.unload()
        self.question_evaluator.unload()
    
if __name__ == "__main__":
    import asyncio
    async def test_integrated_question_generation():
        integrated_service = IntegratedQuestionGeneration()
        document_text = "This is a sample document text about Apple Inc. and its various products and services."
        questions = await integrated_service.generate_questions(document_text)
        print("Generated Questions:", questions)
    
    asyncio.run(test_integrated_question_generation())