import spacy
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer, util
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
            self.nlp = spacy.load("en_core_web_lg")
            self.model = SentenceTransformer('paraphrase-MiniLM-L6-v2')  # Using Sentence-BERT for similarity
        except Exception as e:
            logger.error(f"Error initializing DocumentSegmenter: {e}")
            raise

    async def segment_document(self, result: List[Dict[str, Any]]) -> List[Segment]:
        """
        Segment a document into smaller units (e.g., sentences, tables, lists, figures) and establish relationships between them.

        Args:
            result (List[Dict[str, Any]]): The result of processing the document.

        Returns:
            List[Segment]: A list of Segment instances representing the segmented units.

        Raises:
            Exception: If there's an error during the segmentation process.
        """
        try:
            # Combine text from all files
            text = "\n".join([doc['text'] for doc in result])
            
            # Step 1: Segment the text using spaCy
            segments = await self._segment_with_spacy(text)
            
            # Step 2: Identify and segment non-linear elements (like tables, figures, lists)
            segments += await self._segment_non_linear_elements(result)
            
            # Step 3: Add relationships based on semantic similarity and context
            await self._add_relationships(segments)

            return segments
        except Exception as e:
            logger.error(f"Error segmenting document: {e}")
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

    async def _segment_non_linear_elements(self, result: List[Dict[str, Any]]) -> List[Segment]:
        """
        Segment non-linear elements like tables, lists, or figures.

        Args:
            result (List[Dict[str, Any]]): The result of processing the document.

        Returns:
            List[Segment]: A list of Segment instances representing the non-linear elements.
        """
        try:
            segments = []
            serial_counter = 1

            # Handle Tables
            if "tables" in result:
                for table_index, table in enumerate(result["tables"]):
                    table_text = f"Table {table_index + 1}: {table['caption']}"
                    segments.append(Segment(
                        serial=serial_counter,
                        text=table_text,
                        confidence=1.0,
                        relationship_type="non_linear"
                    ))
                    serial_counter += 1

                    # Segmenting the table content
                    for row_index, row in enumerate(table.get("rows", [])):
                        row_text = " | ".join(row)
                        segments.append(Segment(
                            serial=serial_counter,
                            text=f"Table {table_index + 1}, Row {row_index + 1}: {row_text}",
                            confidence=1.0,
                            relationship_type="non_linear_row"
                        ))
                        serial_counter += 1

            # Handle Figures
            if "figures" in result:
                for figure_index, figure in enumerate(result["figures"]):
                    figure_text = f"Figure {figure_index + 1}: {figure['caption']}"
                    segments.append(Segment(
                        serial=serial_counter,
                        text=figure_text,
                        confidence=1.0,
                        relationship_type="non_linear"
                    ))
                    serial_counter += 1

            # Handle Lists
            if "lists" in result:
                for list_index, list_items in enumerate(result["lists"]):
                    for item_index, item in enumerate(list_items):
                        item_text = f"List {list_index + 1}, Item {item_index + 1}: {item}"
                        segments.append(Segment(
                            serial=serial_counter,
                            text=item_text,
                            confidence=1.0,
                            relationship_type="non_linear_list_item"
                        ))
                        serial_counter += 1

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
        if text1.strip().endswith(":"):
            return True
        return False

# Example Usage:
if __name__ == "__main__":
    # Initialize the DocumentSegmenter
    segmenter = DocumentSegmenter()

    # Process the document and segment it
    result = [
        {
            "text": "This is the first sentence. This is the second sentence."
        },
        {
            "tables": [
                {"caption": "Table 1", "rows": [["A", "B"], ["C", "D"]]}
            ],
            "figures": [
                {"caption": "Figure 1"}
            ],
            "lists": [
                ["Item 1", "Item 2"]
            ]
        }
    ]
    segments = segmenter.segment_document(result)

    # Print the segmented units
    for segment in segments:
        print(f"Segment {segment.serial}: {segment.text} (Relates to: {segment.relates_to}, Type: {segment.relationship_type})")