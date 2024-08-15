# /app/services/rag/integrated_question_generation.py

from typing import List
from app.services.tfidf_extraction import TFIDFExtractor
from app.services.entity_recognition import EntityRecognizer
from app.services.topic_modeling.pipeline import TopicModelingPipeline
from app.services.rag.questions.gpt4_question_generator import GPT4QuestionGenerator
from app.config import settings
import asyncio

class IntegratedQuestionGeneration:
    def __init__(self):
        # self.entity_recognizer = EntityRecognizer()
        # self.topic_modeling_pipeline = TopicModelingPipeline(num_topics=5, passes=10)
        # self.tfidf_extractor = TFIDFExtractor()
        self.question_generator = GPT4QuestionGenerator(api_key=settings.OPENAI_API_KEY)

    async def generate_questions(self, entity_words: List[str], topic_words: List[str], tfidf_keywords: List[str]) -> List[str]:
        """
        Integrates entities, topics, and TF-IDF keywords to generate questions.

        Args:
            document_text (str): The text of the document.

        Returns:
            List[str]: A list of generated questions.
        """
        # # Step 1: Extract Entities (Await the asynchronous call)
        # entities = await self.entity_recognizer.recognize_entities(document_text)
        # print(f"Entities: {entities}")

        # # Step 2: Extract Topics
        # topics = self.topic_modeling_pipeline.run([document_text])
        # print(f"Topics: {topics}")

        # Step 3: Extract TF-IDF Keywords
        # tfidf_keywords = await self.tfidf_extractor.extract_keywords(document_text)
        # print(f"TF-IDF Keywords: {tfidf_keywords}")

        # Step 4: Combine Entities, Topics, and TF-IDF Keywords
        # combined_keywords = list(set([entity.word for entity in entities] +
        #                               [word for topic in topics for word in topic.words] +
        #                               tfidf_keywords))
        combined_keywords = list(set(entity_words + topic_words + tfidf_keywords))
        print(f"Combined Keywords: {combined_keywords}")

        # Step 5: Generate Questions using GPT-4 (Await the asynchronous call)
        questions = await self.question_generator.generate_questions(combined_keywords)
        return questions

