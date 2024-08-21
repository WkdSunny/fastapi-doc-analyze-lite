# /app/services/propmt_engine/entity_recognition.py
"""
This module defines the functions for extracting entities from text segments.
"""

from typing import List, Dict, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.services.llm_clients.openai import send_openai_request
from app.models.rag_model import Segment, Entity
from app.utils.llm_utils import CountTokens, clean_prompt
from app.config import logger

# Define a threshold for determining if segments are related
# SIMILARITY_THRESHOLD = 0.5

# async def are_segments_related(segment1: str, segment2: str) -> bool:
#     """
#     Determine if two segments of text are related based on cosine similarity.

#     Args:
#         segment1 (str): The first text segment.
#         segment2 (str): The second text segment.

#     Returns:
#         bool: True if the segments are related, False otherwise.
#     """
#     try:
#         segments = [segment1, segment2]
#         vectorizer = TfidfVectorizer().fit_transform(segments)
#         similarity_matrix = cosine_similarity(vectorizer[0:1], vectorizer[1:2])
#         return similarity_matrix[0][0] > SIMILARITY_THRESHOLD
#     except ValueError as e:
#         logger.error(f"Vectorization failed: {e}")
#         return False

# async def group_related_segments(segments: List[Segment]) -> List[List[Segment]]:
#     """
#     Group related segments of text together.

#     Args:
#         segments (List[str]): A list of text segments.

#     Returns:
#         List[List[str]]: A list of groups, each containing related text segments.
#     """
#     grouped_segments = []
#     used_indices = set()

#     for i in range(len(segments)):
#         if i in used_indices:
#             continue
#         current_group = [segments[i]]
#         for j in range(i + 1, len(segments)):
#             if j not in used_indices and await are_segments_related(segments[i], segments[j]):
#                 current_group.append(segments[j])
#                 used_indices.add(j)
#         grouped_segments.append(current_group)

#     return grouped_segments

async def get_entities(segments: str) -> Optional[Entity]:
    """
    Extract entities from the given text using the OpenAI API.

    Args:
        text (str): The text from which to extract entities.
        segment_serial (int): The serial number of the segment this entity belongs to.

    Returns:
        Optional[str]: A string containing the entities in CSV format, or None if extraction fails.
    """
    # Define the system prompt for the LLM to understand its role
    system_prompt = (
        "You are an AI that specializes in entity extraction. "
        "You have been given a segment of text and are asked to extract and categorize all entities from it. "
        "Your goal is to accurately identify, extract, and categorize all entities from the text. "
        "Remember, this is a programmatic interaction, not a conversation with an AI."
    )

    # Define the user prompt with instructions and requirements
    user_prompt = (
        f"""
            Extract and categorize all entities from the following segment lsit of text:
            <segment list>
            "{segments}"
            </segment list>

            Information:
            - The text inside the xml tags <segment list> and </segment list> is the text from which you need to extract entities.
            - Each segment inside the xml tags <segment list> and </segment list> is a separate text segment.
            - Each segment looks like - <segment id='3' relates_to='2' relationship_type='contrasts'>1. LENDER NAME AND ADDRESS</segment>.
            - Each segment has been enclosed within the xml tags <segment> and </segment>.
            - Each segment has further attributes like id, relates_to, and relationship_type. 
              That relates to the segment id, the segment it relates to, and the type of relationship respectively.

            Requirements:
            - Extract and categorize all entities from the given text accurately.
            - For each extracted and categorized entity
                + Provide a short description and determine the context in which it appears.
                + Provide a segment serial number to indicate which segment it belongs to.
            - Return the data in csv format. Use pipe (|) as the delimiter.

            Example: (This is for guidance, This is not an exhaustive list)
            category|entity|entity_description|segment_serial
            PER|John Doe|This person is a banker|1
            LOC|New York|This is the city where he lives|5
            ORG|Google|This is one of the companies he worked for|10
            DATE|May 30, 2015|This is the date of the event|12
            DATE|2015-12-17T20:09:35|This is the date and time of the event|12
            DATE|08/18/1994|This is the date of birth of the person|15
            NUM|100001168|This is a number associated with the person|23
            AMT|$100,000|This is the amount of money he earns|55
            EVENT|World War II|This is the event where his grandfather died|96

            Instructions:
            - While the example above is a simple one, the text you will be given may contain more complex entities.
            - There will be more categories than the example above.
            - Try to assign entities to caterogies as accurately and closely as possible, so that it best matches the entity.
            - Do not assign everything apart from ORG, PER, LOC into Miscellaneous (MISC).
            - Use additional categories like DATE, NUMBER, ADDRESS, etc., as needed.
            - Ensure each entity is categorized as accurately as possible.
            - Make sure that the context is not lost while extracting the entities.
            - Do not extract or repeat same entities unnecessarily. Entities should be unique.
            - Use short codes for the categories: PER (Person), LOC (Location), ORG (Organization), DATE, NUM (Number), AMT (Amount), ADDR (Address), PHN (Phone), etc.
            - Descripttion should be short but presize and to the point.
            - Use the format above to return the entities.
        """
    )

    # Prepare the messages for the OpenAI API request
    messages = [
        {"role": "system", "content": clean_prompt(system_prompt)},
        {"role": "user", "content": clean_prompt(user_prompt)}
    ]

    # Payload for the API request
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": messages,
        "max_tokens": 1000,
        "temperature": 0.0
    }

    try:
        # Send the request to OpenAI and get the response
        raw_response = await send_openai_request(api_key=None, messages=messages, payload=payload)
        logger.debug(f"OpenAI response: {raw_response}")

        # Check if the response is successful and contains the required data
        if raw_response.get('success'):
            response = raw_response.get('response')
            if response:  # Ensure response is not None before proceeding
                usage = CountTokens(response.get('usage'))
                if 'choices' in response and isinstance(response['choices'], list):
                    choice = response['choices'][0]
                    if 'message' in choice and 'content' in choice['message']:
                        entities = choice['message']['content']
                        return {
                            "entities": entities.strip(), 
                            "token_usage": usage
                        }
                    else:
                        logger.error(f"'message' or 'content' key not found in the response choice: {choice}")
                else:
                    logger.error(f"'choices' key not found or not a list in the response: {response}")
            else:
                logger.error("No 'response' found in raw_response.")
        else:
            # Log the error message from the response
            logger.error(f"Failed to extract entities: {response.get('error')}")
            return None
    except Exception as e:
        # Catch any exceptions during the process and log them
        logger.exception(f"Exception occurred during entity extraction: {str(e)}")
        return None

# async def extract_entities_from_segments(segments: List[str]) -> List[str]:
#     """
#     Group related segments and extract entities from each group.

#     Args:
#         segments (List[str]): A list of text segments.

#     Returns:
#         List[str]: A list of extracted entities from each group.
#     """
#     # Group related segments
#     grouped_segments = await group_related_segments(segments)

#     # Initialize a list to hold all entities
#     all_entities = []

#     for group in grouped_segments:
#         # Combine the segments in the group
#         combined_text = " | ".join(group)

#         # Extract entities from the combined text
#         entity_result = await get_entities(combined_text)
#         if entity_result:
#             all_entities.append(entity_result["entities"])

#     return all_entities

# async def handle_entity(document_id: str, segments: List[Segment]) -> Dict[str, Optional[str]]:
#     """
#     Perform entity recognition on grouped segments.

#     Args:
#         document_id (str): The ID of the document being processed.
#         segments (List[Segment]): A list of Segment objects.

#     Returns:
#         Dict[str, Optional[str]]: A dictionary containing the entities and token usage.
#     """
#     try:
#         # Combine all segments into one text block
#         combined_text = " | ".join([segment.text for segment in segments])
#         logger.info(f"Document ID: {document_id}, Combined Text: {combined_text}")

#         # Extract entities from the combined text
#         raw_entities = await get_entities(combined_text)
#         entities_csv = raw_entities["entities"]
#         token_usage = raw_entities["token_usage"]

#         # Parse the entities CSV content
#         parsed_entities = await parse_csv_content(entities_csv)

#         # Convert parsed entities into Entity objects and insert them into the database
#         entity_list = []
#         for entity_data in parsed_entities:
#             entity = Entity(
#                 entity_type=entity_data.get("category"),
#                 text=entity_data.get("entity"),
#                 description=entity_data.get("entity_description"),
#                 segment_serial=None  # We can add logic to link this to a segment if needed
#             )
#             entity_list.append(entity)
        
#         await insert_entities(document_id, entity_list)
#         await insert_token_consumption(document_id, "OpenAI", "Entity Recognition", token_usage)

#         return {
#             "entities": entity_list,
#             "token_usage": token_usage
#         }

#     except Exception as e:
#         logger.error(f"Failed to extract entities for document ID: {document_id}: {e}")
#         raise


# Example usage:
if __name__ == "__main__":
    async def main():
        segments = """
            <segment list><segment id='0' relates_to='None' relationship_type='None'>DEPARTMENT OF HOMELAND SECURITY
            FEDERAL EMERGENCY MANAGEMENT AGENCY
            STANDARD FLOOD HAZARD DETERMINATION FORM (SFHDF)</segment>
            <segment id='1' relates_to='0' relationship_type='contrasts'>See the attached
            instructions</segment>
            <segment id='2' relates_to='1' relationship_type='contrasts'>O.M.B. No. 1660-0040
            Expires May 30, 2015</segment>
            <segment id='3' relates_to='2' relationship_type='contrasts'>1. LENDER NAME AND ADDRESS</segment>
            <segment id='4' relates_to='3' relationship_type='contrasts'>2. COLLATERAL  (Building/Mobile Home/Property)</segment></segment list>
        """

        # Extract entities from segments
        entities = await get_entities(segments)

        logger.info(f"Entities extracted from segments: {entities}")

    import asyncio
    asyncio.run(main())
