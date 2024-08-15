# /app/services/document_classification.py
"""
This module defines the document classification service for the FastAPI application.
"""

import gc
import torch
import asyncio
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from transformers import BertTokenizer, BertForSequenceClassification, pipeline
from app.models.rag_model import Classification
from app.config import logger

class DocumentClassifier:
    """
    A service class for classifying documents using a BERT-based model.

    Attributes:
        tokenizer (BertTokenizer): Tokenizer for text processing.
        model (BertForSequenceClassification): Model for sequence classification.
        device (str): Device to run the model on, either 'cuda' or 'cpu'.
    """
    
    def __init__(self):
        """
        Initializes the DocumentClassifier service class.

        Raises:
            Exception: If there's an error during initialization.
        """
        try:
            self.tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
            self.model = BertForSequenceClassification.from_pretrained("bert-base-uncased")
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device)
            logger.info(f"DocumentClassifier initialized with device: {self.device}")
        except Exception as e:
            logger.error(f"Error initializing DocumentClassifier: {e}")
            raise

    def chunk_text(self, text: str, chunk_size: int = 512) -> List[str]:
        """
        Splits the input text into chunks of a specified size.

        Args:
            text (str): The input text to be chunked.
            chunk_size (int): The maximum size of each chunk in tokens.

        Returns:
            List[str]: A list of text chunks.

        Raises:
            Exception: If there's an error during the text chunking process.
        """
        try:
            tokens = self.tokenizer.tokenize(text)
            token_chunks = [tokens[i:i + chunk_size] for i in range(0, len(tokens), chunk_size)]
            return [" ".join(chunk[:chunk_size]) for chunk in token_chunks]
        except Exception as e:
            logger.error(f"Error chunking text: {e}")
            raise

    def classify_chunks(self, text_chunks: List[str]) -> List[Dict[str, Any]]:
        """
        Classifies each chunk of text using a text classification pipeline.

        Args:
            text_chunks (List[str]): A list of text chunks to be classified.

        Returns:
            List[Dict[str, Any]]: A list of classification results for each chunk.

        Raises:
            Exception: If there's an error during the classification process.
        """
        try:
            classification_pipeline = pipeline(
                "text-classification",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1,
                max_length=512,
                truncation=True,
                clean_up_tokenization_spaces=True
            )
            return [classification_pipeline(chunk) for chunk in text_chunks]
        except Exception as e:
            logger.error(f"Error classifying text chunks: {e}")
            raise

    async def classify_document(self, text: str) -> Classification:
        """
        Classifies an entire document by breaking it into chunks and aggregating the results.

        Args:
            text (str): The text content of the document to be classified.

        Returns:
            Classification: The best classification label and its confidence score.

        Raises:
            Exception: If there's an error during the document classification process.
        """
        try:
            chunks = self.chunk_text(text)
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as pool:
                classification_results = await loop.run_in_executor(pool, self.classify_chunks, chunks)

            combined_scores = {}
            for result in classification_results:
                for classification in result:
                    label = classification['label']
                    score = classification['score']
                    combined_scores[label] = combined_scores.get(label, 0) + score

            # Average the scores across all chunks
            for label in combined_scores:
                combined_scores[label] /= len(classification_results)

            # Determine the label with the highest average score
            best_label = max(combined_scores, key=combined_scores.get)
            return Classification(label=best_label, score=combined_scores[best_label])
        except Exception as e:
            logger.error(f"Error classifying document: {e}")
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


            logger.info("DocumentClassifier resources have been unloaded.")
        except Exception as e:
            logger.error(f"Error unloading DocumentClassifier resources: {e}")
            raise

if __name__ == "__main__":
    # Example usage of the DocumentClassifier class
    classifier = DocumentClassifier()
    text = "This is a sample document text. It should be classified by the model."
    classification_result = asyncio.run(classifier.classify_document(text))
    print(classification_result)
    
    # Unload resources after use
    classifier.unload()