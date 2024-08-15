# /app/services/question_generation/rag_question_generator.py
"""
This module defines the RAG-based question generation service for the FastAPI application.
"""

from transformers import RagTokenizer, RagTokenForGeneration
import gc
import torch
from app.config import logger
from typing import List
from app.models.rag_model import RAGQuestionGenerator as ReqQuestion

class RAGQuestionGenerator:
    """
    A service class for generating questions based on entities and topics using the RAG model.

    Attributes:
        tokenizer (RagTokenizer): Tokenizer for input processing.
        model (RagTokenForGeneration): RAG model for question generation.
        device (str): Device to run the model on (CPU or GPU).
    """
    
    def __init__(self):
        """
        Initializes the RAGQuestionGenerator service class.

        Raises:
            Exception: If there's an error during initialization.
        """
        try:
            model_name = "facebook/rag-token-nq"
            self.tokenizer = RagTokenizer.from_pretrained(model_name)
            self.model = RagTokenForGeneration.from_pretrained(model_name)
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device)
            logger.info(f"RAGQuestionGenerator initialized with device: {self.device}")
        except Exception as e:
            logger.error(f"Error initializing RAGQuestionGenerator: {e}")
            raise

    def generate_questions(self, entities: List[str], topics: List[str]):
        """
        Generates questions based on the provided entities and topics.

        Args:
            entities (List[str]): A list of entities extracted from the document.
            topics (List[str]): A list of topics identified in the document.

        Returns:
            List[Question]: A list of generated questions.

        Raises:
            Exception: If there's an error during the question generation process.
        """
        try:
            context = " ".join(entities + topics)
            logger.debug(f"Context for question generation: {context}")

            if not context.strip():
                logger.error("Context is empty. Cannot generate questions.")
                raise ValueError("Context is empty. Cannot generate questions.")

            # Tokenize input context
            input_ids = self.tokenizer(context, return_tensors="pt").input_ids.to(self.device)
            logger.debug(f"Tokenized input_ids: {input_ids}")
            logger.debug(f"Shape of input_ids: {input_ids.shape}")
            logger.debug(f"Device of input_ids: {input_ids.device}")
            logger.debug(f"First few tokens in input_ids: {input_ids[:, :10]}")

            if input_ids is None:
                logger.error("Tokenization failed. input_ids is None.")
                raise ValueError("Tokenization failed. input_ids is None.")

            # Generate questions
            outputs = self.model.generate(input_ids=input_ids)
            logger.debug(f"Generated outputs: {outputs}")

            if outputs is None or not outputs:
                logger.error("Model generation failed. outputs is None.")
                raise ValueError("Model generation failed. outputs is None.")

            # Decode the generated questions
            questions = [self.tokenizer.decode(output, skip_special_tokens=True) for output in outputs]

            return questions

        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            raise

    def unload(self):
        """
        Unloads the model and tokenizer, freeing up memory.
        """
        try:
            del self.model
            del self.tokenizer
            if self.device == "cuda":
                torch.cuda.empty_cache()
            else:
                gc.collect()
            logger.info("RAGQuestionGenerator resources have been unloaded.")
        except Exception as e:
            logger.error(f"Error unloading RAGQuestionGenerator resources: {e}")
            raise

if __name__ == "__main__":
    # Example usage of the RAGQuestionGenerator class
    question_generator = RAGQuestionGenerator()
    entities = ["entity1", "entity2"]
    topics = ["topic1", "topic2"]
    questions = question_generator.generate_questions(entities, topics)
    for question in questions:
        print(question)

    # Unload resources after use
    question_generator.unload()