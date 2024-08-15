# /app/services/entity_recognition.py
"""
This module defines the entity recognition service for the FastAPI application.
"""

import gc
import torch
import asyncio
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from transformers import BertTokenizer, BertForTokenClassification, pipeline
from app.models.rag_model import Entity
from app.config import logger

class EntityRecognizer:
    """
    A service class for recognizing named entities in a given text using a BERT-based model.

    Attributes:
        tokenizer (BertTokenizer): Tokenizer for text processing.
        model (BertForTokenClassification): Model for token classification.
    """
    
    def __init__(self):
        """
        Initializes the EntityRecognizer service class.

        Raises:
            Exception: If there's an error during initialization.
        """
        try:
            self.tokenizer = BertTokenizer.from_pretrained("dbmdz/bert-large-cased-finetuned-conll03-english")
            self.model = BertForTokenClassification.from_pretrained("dbmdz/bert-large-cased-finetuned-conll03-english")
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        except Exception as e:
            logger.error(f"Error initializing EntityRecognizer: {e}")
            raise

    def run_ner_pipeline(self, text: str) -> List[Dict[str, Any]]:
        """
        Runs the Named Entity Recognition (NER) pipeline on the input text.

        Args:
            text (str): The input text for entity recognition.

        Returns:
            List[Dict[str, Any]]: A list of entities recognized in the text.

        Raises:
            Exception: If there's an error during the NER process.
        """
        try:
            ner_pipeline = pipeline("ner", model=self.model, tokenizer=self.tokenizer, device=self.device)
            return ner_pipeline(text)
        except Exception as e:
            logger.error(f"Error running NER pipeline: {e}")
            raise

    async def recognize_entities(self, text: str) -> List[Entity]:
        """
        Recognizes entities in the input text asynchronously.

        Args:
            text (str): The input text for entity recognition.

        Returns:
            List[Entity]: A list of recognized entities.

        Raises:
            Exception: If there's an error during the entity recognition process.
        """
        try:
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as pool:
                entities = await loop.run_in_executor(pool, self.run_ner_pipeline, text)
            recognized_entities: List[Entity] = [
                Entity(
                    serial=index,
                    word=entity['word'],
                    entity=entity['entity'],
                    score=float(entity['score']),
                    start=int(entity['start'] if entity['start'] is not None else 0),
                    end=int(entity['end'] if entity['end'] is not None else 0)
                )
                for index, entity in enumerate(entities)
            ]
            return recognized_entities
        except Exception as e:
            logger.error(f"Error recognizing entities: {e}")
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
            logger.info("EntityRecognizer resources have been unloaded.")
        except Exception as e:
            logger.error(f"Error unloading EntityRecognizer resources: {e}")
            raise

if __name__ == "__main__":
    # Example usage of the EntityRecognizer class
    recognizer = EntityRecognizer()
    text = "Apple is a company based in Cupertino, California."
    entities = asyncio.run(recognizer.recognize_entities(text))
    for entity in entities:
        print(entity)
    recognizer.unload()
