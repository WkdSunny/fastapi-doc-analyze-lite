# /app/services/prompt_engine/document_segmentation.py
"""
This module defines a service class for segmenting documents into smaller units.
"""

import re
import spacy
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer, util
import app.services.db.insert as insert_segments
from app.models.rag_model import Segment
from app.config import logger


class DocumentSegmenter:
    """
    A service class for segmenting documents into smaller units (e.g., sentences, tables, figures, lists).
    This class also establishes relationships between segments, enhancing context and relevance.
    """

    def __init__(self):
        """
        Initializes the DocumentSegmenter service class.
        Loads necessary NLP models for text processing and similarity analysis.
        """
        try:
            self.nlp = spacy.load("en_core_web_sm")
            self.model = SentenceTransformer('paraphrase-MiniLM-L6-v2')  # Using Sentence-BERT for similarity
        except Exception as e:
            logger.error(f"Error initializing DocumentSegmenter: {e}")
            raise

    async def segment_document(self, result: Dict[str, Any], document_type: str) -> List[Segment]:
        """
        Segment a document into smaller units (e.g., sentences, tables, lists, figures) and establish relationships between them.

        Args:
            result (Dict[str, Any]): The result of processing the document.
            document_type (str): The type of document being processed (e.g., "text", "pdf").

        Returns:
            List[Segment]: A list of Segment instances representing the segmented units.

        Raises:
            Exception: If there's an error during the segmentation process.
        """
        try:
            text = result.get("text", "")
            segments = []

            if "pdf" in document_type or "image" in document_type:
                # Run bounding box segmentation directly
                segments += await self._segment_with_bounding_boxes(result)
            else:
                # Run spaCy segmentation directly
                segments += await self._segment_with_spacy(text)

            # Identify and segment non-linear elements (like tables, figures, lists)
            segments += await self._segment_non_linear_elements(result)

            # Add relationships based on semantic similarity and context
            await self._add_relationships(segments)

            return segments
        except Exception as e:
            logger.error(f"Error segmenting document: {e}")
            raise

    async def _segment_with_bounding_boxes(self, result: Dict[str, Any]) -> List[Segment]:
        """
        Segment a document using bounding box information. Used for PDFs or image-based documents.

        Args:
            result (Dict[str, Any]): The result of processing the document.

        Returns:
            List[Segment]: A list of Segment instances representing the segmented units.
        """
        try:
            logger.info("Segmenting document using bounding boxes.")
            segments = [
                Segment(
                    serial=index,
                    text=bbox["text"],
                    confidence=float(bbox["confidence"])
                )
                for index, bbox in enumerate(result.get("bounding_boxes", []))
            ]
            return segments
        except Exception as e:
            logger.error(f"Error in bounding box segmentation: {e}")
            raise

    async def _segment_with_spacy(self, text: str) -> List[Segment]:
        """
        Segment a document using spaCy's sentence segmentation.

        Args:
            text (str): The text content of the document.

        Returns:
            List[Segment]: A list of Segment instances representing the segmented units.
        """
        try:
            logger.info("Segmenting document using spaCy.")
            doc = self.nlp(text)
            segments = [
                Segment(
                    serial=index + 1,
                    text=sent.text.strip(),
                    confidence=1.0  # spaCy's NLP output is deterministic, so full confidence
                )
                for index, sent in enumerate(doc.sents)
            ]
            logger.info(f"Completed spaCy segmentation with {len(segments)} segments.")
            return segments
        except Exception as e:
            logger.error(f"Error in spaCy text segmentation: {e}")
            raise

    async def _segment_non_linear_elements(self, result: Dict[str, Any]) -> List[Segment]:
        """
        Segment non-linear elements like tables, lists, or figures.

        Args:
            result (Dict[str, Any]): The result of processing the document.

        Returns:
            List[Segment]: A list of Segment instances representing the non-linear elements.
        """
        try:
            segments = []

            # Handle Tables
            if "tables" in result:
                for table_index, table in enumerate(result["tables"]):
                    table_text = f"Table {table_index + 1}: {table['caption']}"
                    segments.append(Segment(
                        serial=len(segments),
                        text=table_text,
                        confidence=1.0,
                        relationship_type="non_linear"
                    ))

                    # Segmenting the table content
                    for row_index, row in enumerate(table.get("rows", [])):
                        row_text = " | ".join(row)
                        segments.append(Segment(
                            serial=len(segments),
                            text=f"Table {table_index + 1}, Row {row_index + 1}: {row_text}",
                            confidence=1.0,
                            relationship_type="non_linear_row"
                        ))

            # Handle Figures
            if "figures" in result:
                for figure_index, figure in enumerate(result["figures"]):
                    figure_text = f"Figure {figure_index + 1}: {figure['caption']}"
                    segments.append(Segment(
                        serial=len(segments),
                        text=figure_text,
                        confidence=1.0,
                        relationship_type="non_linear"
                    ))

            # Handle Lists
            if "lists" in result:
                for list_index, list_items in enumerate(result["lists"]):
                    for item_index, item in enumerate(list_items):
                        item_text = f"List {list_index + 1}, Item {item_index + 1}: {item}"
                        segments.append(Segment(
                            serial=len(segments),
                            text=item_text,
                            confidence=1.0,
                            relationship_type="non_linear_list_item"
                        ))

            logger.info(f"Completed non-linear element segmentation with {len(segments)} segments.")
            return segments
        except Exception as e:
            logger.error(f"Error segmenting non-linear elements: {e}")
            raise

    async def _add_relationships(self, segments: List[Segment]) -> None:
        """
        Add relationships between segments based on semantic similarity, context, and specific cases.

        Args:
            segments (List[Segment]): List of segmented units.

        Returns:
            None: Modifies the segments list in place.
        """
        try:
            embeddings = self.model.encode([segment.text for segment in segments])

            for i in range(1, len(segments)):
                # Handle specific cases where segments should be inherently related
                if self._is_label_value_pair(segments[i - 1].text, segments[i].text):
                    segments[i].relates_to = segments[i - 1].serial
                    segments[i].relationship_type = "label_value"
                    continue

                if segments[i].relationship_type == "non_linear":
                    continue  # Skip non-linear elements for direct relationships

                similarity = util.cos_sim(embeddings[i], embeddings[i - 1]).item()

                segments[i].relates_to = segments[i - 1].serial

                # Determine the type of relationship based on similarity score
                if similarity > 0.8:  # High similarity indicates continuation or elaboration
                    segments[i].relationship_type = "elaborates"
                elif similarity < 0.5:  # Low similarity might indicate contrast
                    segments[i].relationship_type = "contrasts"
                else:
                    segments[i].relationship_type = "follows"

                # Handle non-linear elements (like tables) contextually
                for j in range(len(segments)):
                    if segments[j].relationship_type == "non_linear":
                        context_similarity = util.cos_sim(embeddings[j], embeddings[i]).item()
                        if context_similarity > 0.6:
                            segments[j].relates_to = segments[i].serial
                            segments[j].relationship_type = "contextual_reference"

            logger.info("Completed adding relationships between segments.")
        except Exception as e:
            logger.error(f"Error adding relationships between segments: {e}")
            raise

    def _is_label_value_pair(self, text1: str, text2: str) -> bool:
        """
        Determine if two segments represent a label-value pair (e.g., "Address:" followed by the actual address).

        Args:
            text1 (str): The first segment's text.
            text2 (str): The second segment's text.

        Returns:
            bool: True if the segments represent a label-value pair, False otherwise.
        """
        # Simple heuristic: if the first segment ends with a colon and the second does not start with a capital letter
        if text1.strip().endswith(":"):
            return True
        return False

if __name__ == "__main__":
    import asyncio
    
    # Example usage of the DocumentSegmenter class
    logger.info("Initializing DocumentSegmenter for testing...")
    segmenter = DocumentSegmenter()

    result = {
        "text": "Introduction to sustainable energy. This is a sample document. It contains multiple sentences. Each sentence is a segment. However, there are some differences.",
        "tables": [{"caption": "Energy Investments by Year", "rows": [["Year", "Solar", "Wind", "Hydro"], ["2020", "100MW", "150MW", "200MW"], ["2021", "110MW", "160MW", "210MW"]]}],
        "figures": [{"caption": "Growth of Renewable Energy Sources"}],
        "lists": [["Solar energy", "Wind energy", "Hydroelectric energy"]]
    }
    
    logger.info("Starting document segmentation...")
    segments = asyncio.run(segmenter.segment_document(result, "text"))
    
    logger.info("Document segmentation complete. Printing segments...")
    for seg in segments:
        print(seg)

    logger.info("Document segmentation test completed.")
