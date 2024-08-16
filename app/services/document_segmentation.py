# /app/services/document_segmentation.py
"""
This module defines the document segmentation service for the FastAPI application.
"""
import gc
import spacy
import torch
from typing import List, Dict, Any
from app.models.rag_model import Segment, BoundingBox
from app.models.pdf_model import PDFTextResponse
from app.config import logger

class DocumentSegmenter:
    """
    A service class for segmenting documents into smaller units (e.g., sentences).

    Attributes:
        nlp (spacy.Language): A spaCy NLP model for text segmentation.
    """
    def __init__(self):
        """
        Initializes the DocumentSegmenter service class.

        Raises:
            Exception: If there's an error during initialization.
        """
        try:
            # Load the spaCy model for text segmentation
            self.nlp = spacy.load("en_core_web_sm")
        except Exception as e:
            logger.error(f"Error initializing DocumentSegmenter: {e}")
            raise

    async def segment_document(self, result: Dict[str, Any], document_type: str) -> List[Segment]:
        """
        Segment a document into smaller units (e.g., sentences or bounding boxes).

        Args:
            result (Dict[str, Any]): The result of processing the document.
            document_type (str): The type of document being processed.

        Returns:
            List[Segment]: A list of Segment instances representing the segmented units.

        Raises:
            Exception: If there's an error during the segmentation process.
        """
        try:
            text = result["text"]
            segments = []
            
            if "pdf" in document_type or "image" in document_type:
                segments = self._segment_with_bounding_boxes(result)
            else:
                segments = self._segment_with_spacy(text)

            return segments
        except Exception as e:
            logger.error(f"Error segmenting document: {e}")
            raise

    def _segment_with_bounding_boxes(self, result: Dict[str, Any]) -> List[Segment]:
        """
        Segment a document using bounding box information. Used for PDFs or image-based documents.

        Args:
            result (Dict[str, Any]): The result of processing the document.

        Returns:
            List[Segment]: A list of Segment instances representing the segmented units.

        Raises:
            Exception: If there's an error during the segmentation process.
        """
        try:
            logger.info("Segmenting document using bounding boxes.")
            segments = [
                Segment(
                    serial=index,
                    page=bbox["page"],
                    bbox=BoundingBox(
                        left=float(bbox["bbox"]["left"]),
                        top=float(bbox["bbox"]["top"]),
                        width=float(bbox["bbox"]["width"]),
                        height=float(bbox["bbox"]["height"]),
                    ),
                    text=bbox["text"],
                    confidence=float(bbox["confidence"])  # Convert to regular float
                )
                for index, bbox in enumerate(result["bounding_boxes"])
            ]
            return segments
        except Exception as e:
            logger.error(f"Error in bounding box segmentation: {e}")
            raise

    def _segment_with_spacy(self, text: str) -> List[Segment]:
        """
        Segment a document using spaCy's sentence segmentation.

        Args:
            text (str): The text content of the document.

        Returns:
            List[Segment]: A list of Segment instances representing the segmented units.

        Raises:
            Exception: If there's an error during the segmentation process.
        """
        try:
            logger.info("Segmenting document using spaCy.")
            
            doc = self.nlp(text)
            segments = [
                Segment(
                    serial=index,
                    text=sent.text,
                    confidence=1.0  # spaCy's NLP output is deterministic, so full confidence
                )
                for index, sent in enumerate(doc.sents)
            ]
            return segments
        except Exception as e:
            logger.error(f"Error in spaCy text segmentation: {e}")
            raise

    # def unload(self):
    #     """
    #     Unloads the model and tokenizer, freeing up memory.
    #     """
    #     try:
    #         del self.model
    #         del self.tokenizer
    #         if self.device == "cuda":
    #             torch.cuda.empty_cache()
    #         else:
    #             gc.collect()
    #         logger.info("RAGQuestionGenerator resources have been unloaded.")
    #     except Exception as e:
    #         logger.error(f"Error unloading RAGQuestionGenerator resources: {e}")
    #         raise

if __name__ == "__main__":
    import asyncio
    # Example usage of the DocumentSegmenter class
    segmenter = DocumentSegmenter()
    result = {
        "text": "This is a sample document. It contains multiple sentences. Each sentence is a segment."
    }
    segments = asyncio.run(segmenter.segment_document(result, "text"))
    for seg in segments:
        print(seg)
    # segmenter.unload()