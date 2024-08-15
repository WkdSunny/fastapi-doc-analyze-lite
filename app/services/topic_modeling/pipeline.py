# app/services/topic_modeling/topic_modeling_pipeline.py

from typing import List, Dict
from app.services.topic_modeling.preprocessing import TextPreprocessor
from app.services.topic_modeling.lda_modeling import LDAModel

class TopicModelingPipeline:
    def __init__(self, num_topics: int = 5, passes: int = 10):
        self.preprocessor = TextPreprocessor()
        self.lda_modeler = LDAModel(num_topics=num_topics, passes=passes)
    
    def run(self, documents: List[str]) -> Dict[int, List[str]]:
        """
        Run the entire topic modeling pipeline.
        
        Args:
            documents (List[str]): List of raw text documents.
        
        Returns:
            Dict[int, List[str]]: A dictionary of topics with their corresponding words.
        """
        # Preprocess each document
        processed_texts = [self.preprocessor.preprocess_text(doc) for doc in documents]
        
        # Build the LDA model
        lda_model = self.lda_modeler.build_lda_model(processed_texts)
        
        # Get the topics from the LDA model
        topics = self.lda_modeler.get_topics(lda_model)
        
        return topics
