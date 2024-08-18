# /app/utils/date_utils.py
"""
This module provides a function to convert a text string to ISO 8601 date format using SpaCy's NER capabilities.
"""
import spacy
from dateutil.parser import parse as date_parse, ParserError
from typing import Union, List
import asyncio

# Load the SpaCy model
nlp = spacy.load("en_core_web_sm")

async def process_with_spacy(texts: List[str]) -> List[str]:
    """Process a list of texts with SpaCy to extract dates."""
    docs = list(nlp.pipe(texts, disable=["parser", "ner"]))  # Disable unnecessary components for efficiency
    return docs

async def convert_to_iso_date(text: Union[str, List[str]]) -> Union[str, List[str]]:
    """
    Attempt to convert a text string or a list of text strings to ISO 8601 date format using SpaCy's NER capabilities.
    If the text is not recognized as a date, return the original text.
    
    Args:
        text (Union[str, List[str]]): The input text or list of text strings to be checked and possibly converted.
        
    Returns:
        Union[str, List[str]]: The ISO 8601 formatted date(s) if conversion is successful, otherwise the original text(s).
    """
    def convert_date(s: str) -> str:
        """Convert a single detected date to ISO 8601 format."""
        try:
            parsed_date = date_parse(s, fuzzy=True)
            return parsed_date.isoformat()
        except (ParserError, ValueError):
            return s

    if isinstance(text, str):
        # Process a single string
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ == "DATE":
                return convert_date(ent.text)
        return text  # Return the original text if no date entity is found
    elif isinstance(text, list):
        # Process a list of strings asynchronously
        docs = await process_with_spacy(text)
        converted_dates = []
        for doc in docs:
            converted_text = doc.text
            for ent in doc.ents:
                if ent.label_ == "DATE":
                    converted_text = convert_date(ent.text)
            converted_dates.append(converted_text)
        return converted_dates

# Example usage within an asynchronous context
async def process_row(headers, row):
    # Properly await the async function
    converted_row = {header: await convert_to_iso_date(value.strip()) for header, value in zip(headers, row)}
    return converted_row

# Running the example
async def main():
    headers = ["date", "description"]
    row = ["January 01, 2024 at 10:10 AM", "Sample description"]

    converted_row = await process_row(headers, row)
    print("Converted Row:", converted_row)

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
