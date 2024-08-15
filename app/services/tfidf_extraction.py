# /app/services/tfidf_extraction.py

from sklearn.feature_extraction.text import TfidfVectorizer
from typing import List
import asyncio

class TFIDFExtractor:
    def __init__(self, max_features: int = 10):
        self.vectorizer = TfidfVectorizer(min_df=0.0, max_features=max_features, stop_words='english')
    
    async def extract_keywords(self, text: str) -> List[str]:
        """
        Extracts top keywords from the text using TF-IDF.

        Args:
            text (str): The input text.

        Returns:
            List[str]: A list of top keywords based on TF-IDF.
        """
        loop = asyncio.get_event_loop()
        tfidf_matrix = await loop.run_in_executor(None, self.vectorizer.fit_transform, [text])
        feature_array = self.vectorizer.get_feature_names_out()
        tfidf_sorting = await loop.run_in_executor(None, lambda: tfidf_matrix.toarray().flatten().argsort()[::-1])
        
        top_n = tfidf_sorting[:self.vectorizer.max_features]
        return [feature_array[i] for i in top_n]
