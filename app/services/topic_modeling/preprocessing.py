# app/services/topic_modeling/preprocessing.py

import spacy

class TextPreprocessor:
    def __init__(self, model_name: str = "en_core_web_sm"):
        self.nlp = spacy.load(model_name)
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess the text by tokenizing, removing stop words, and lemmatizing.
        
        Args:
            text (str): The input text to preprocess.
        
        Returns:
            str: The preprocessed text.
        """
        doc = self.nlp(text)
        processed_tokens = [
            token.lemma_ for token in doc 
            if not token.is_stop and not token.is_punct
        ]
        return " ".join(processed_tokens)
