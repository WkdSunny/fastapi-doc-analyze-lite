# app/services/topic_modeling/lda_modeling.py

import gensim
from gensim import corpora
from gensim.models.ldamodel import LdaModel
from typing import List, Dict
from app.models.rag_model import Topic

class LDAModel:
    def __init__(self, num_topics: int = 5, passes: int = 10):
        self.num_topics = num_topics
        self.passes = passes
    
    def build_lda_model(self, processed_texts: List[str]) -> LdaModel:
        """
        Build the LDA model based on the processed texts.
        
        Args:
            processed_texts (List[str]): List of preprocessed text documents.
        
        Returns:
            LdaModel: The LDA model.
        """
        # Tokenize the processed texts
        tokenized_texts = [text.split() for text in processed_texts]
        
        # Create a dictionary representation of the documents
        dictionary = corpora.Dictionary(tokenized_texts)
        
        # Convert the documents into a document-term matrix
        corpus = [dictionary.doc2bow(text) for text in tokenized_texts]
        
        # Build the LDA model
        lda_model = LdaModel(
            corpus=corpus,
            id2word=dictionary,
            num_topics=self.num_topics,
            passes=self.passes
        )
        return lda_model

    def get_topics(self, lda_model: LdaModel, num_words: int = 10) -> Dict[int, List[str]]:
        """
        Extract topics from the LDA model.
        
        Args:
            lda_model (LdaModel): The LDA model.
            num_words (int): Number of words to retrieve per topic.
        
        Returns:
            Dict[int, List[str]]: A dictionary of topics with their corresponding words.
        """
        topics = lda_model.show_topics(num_topics=self.num_topics, num_words=num_words, formatted=False)
        topics_dict = {serial: [word for word, _ in words] for serial, words in topics}
        # Convert the dictionary to a list of Topic instances
        topic_instances = [
            Topic(serial=serial, words=words)
            for serial, words in topics_dict.items()
        ]
        return topic_instances
