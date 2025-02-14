# /app/utils/model_utils.py
"""
This module contains utility functions to convert CSV data to JSON.
"""

import csv
from io import StringIO
from app.models.llm_model import ExtractionItem, ExtractionResponse
from app.config import logger

def csv_to_json(csv_content: str) -> ExtractionResponse:
    """
    Convert CSV content to an ExtractionResponse object.
    
    Parameters:
        csv_content (str): The CSV content as a string.
        
    Returns:
        ExtractionResponse: The corresponding ExtractionResponse object.
    """
    # Initialize a list to hold the data items
    data_items = []

    try:
        # Use StringIO to read the CSV content
        csv_reader = csv.DictReader(StringIO(csv_content), delimiter='|')
        logger.debug(f"CSV content: {csv_content}")
        
        for row in csv_reader:
            # Create an ExtractionItem for each row in the CSV
            item = ExtractionItem(
                key=row["Information Key"].strip(),
                matching_key=row["Matching Key"].strip(),
                matching_value=row["Matching Value"].strip(),
                value=row["Value"].strip(),
                additional_comments=row["Addl. Comments"].strip()
            )
            data_items.append(item)
        
    except KeyError as ke:
        logger.error(f"KeyError: {ke}")
        raise ValueError(f"Missing expected column in CSV: {ke}")
    
    except Exception as e:
        logger.error(f"An error occurred while processing the CSV: {str(e)}")
        raise ValueError(f"Failed to process CSV content: {str(e)}")

    # Create an ExtractionResponse with the list of items
    response = ExtractionResponse(data=data_items)
    return response

# Example Usage
if __name__ == "__main__":
    csv_content = """Information Key|Matching Key|Matching Value|Value|Addl. Comments
Loan Number|Loan Number|100001168|100001168|Another comment.
Policy Number|Policy Number|97-B8-5008-1|97-B8-5008-1|This is a comment.
"""
    # Convert the CSV content to an ExtractionResponse object
    response = csv_to_json(csv_content)
    # Print the response in JSON format with indentation for readability
    print(response.json(indent=2))
