from typing import List, Dict, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.services.llm_clients.openai import send_openai_request
from app.utils.llm_utils import CountTokens, clean_prompt
from app.config import logger

# Define a threshold for determining if segments are related
SIMILARITY_THRESHOLD = 0.5

async def are_segments_related(segment1: str, segment2: str) -> bool:
    """
    Determine if two segments of text are related based on cosine similarity.

    Args:
        segment1 (str): The first text segment.
        segment2 (str): The second text segment.

    Returns:
        bool: True if the segments are related, False otherwise.
    """
    try:
        segments = [segment1, segment2]
        vectorizer = TfidfVectorizer().fit_transform(segments)
        similarity_matrix = cosine_similarity(vectorizer[0:1], vectorizer[1:2])
        return similarity_matrix[0][0] > SIMILARITY_THRESHOLD
    except ValueError as e:
        logger.error(f"Vectorization failed: {e}")
        return False

async def group_related_segments(segments: List[str]) -> List[List[str]]:
    """
    Group related segments of text together.

    Args:
        segments (List[str]): A list of text segments.

    Returns:
        List[List[str]]: A list of groups, each containing related text segments.
    """
    grouped_segments = []
    used_indices = set()

    for i in range(len(segments)):
        if i in used_indices:
            continue
        current_group = [segments[i]]
        for j in range(i + 1, len(segments)):
            if j not in used_indices and await are_segments_related(segments[i], segments[j]):
                current_group.append(segments[j])
                used_indices.add(j)
        grouped_segments.append(current_group)

    return grouped_segments

async def get_entities(text: str) -> Optional[str]:
    """
    Extract entities from the given text using the OpenAI API.

    Args:
        text (str): The text from which to extract entities.

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
            Extract and categorize all entities from the following text:
            <text>
            "{text}"
            </text>

            Information:
            - The pipe (|) separated text supplied above, inside xml tags <text></text> are the Segments of text converted from one file.

            Requirements:
            - Extract and categorize all entities from the given text.
            - The entities should be extracted and categorized accurately.
            - For each extracted and categorized entity, provide a short description and determine the context in which it appears.
            - Return the data in csv format. Use pipe (|) as the delimiter.

            Example: (This is for guidance, This is not an exhaustive list)
            entity|text|description
            PER|John Doe|This person is a banker
            LOC|New York|This is the city where he lives
            ORG|Google|This is one of the companies he worked for
            DATE|May 30, 2015|This is the date of the event
            DATE|2015-12-17T20:09:35|This is the date and time of the event
            DATE|08/18/1994|This is the date of birth of the person
            NUM|100001168|This is a number associated with the person
            AMT|$100,000|This is the amount of money he earns
            EVENT|World War II|This is the event where his grandfather died

            Instructions:
            - While the example above is a simple one, the text you will be given may contain more complex entities.
            - There will be more categories than the example above.
            - Ensure that the entities are extracted and categorized accurately.
            - Do not assign everything apart from ORG, PER, LOC into Miscellaneous (MISC).
            - Use additional categories like DATE, NUMBER, ADDRESS, etc., as needed.
            - Ensure each entity is categorized as accurately as possible.
            - Make sure that the context is not lost while extracting the entities.
            - Do not repeat text unnecessarily. Text should be unique.
            - Use short codes for the categories: PER (Person), LOC (Location), ORG (Organization), DATE, NUM (Number), AMT (Amount), etc.
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

# Example usage:
if __name__ == "__main__":
    async def main():
        segments = [
            "John Doe is a software engineer.",
            "He works at Google.",
            "New York is a city in the United States."
        ]

        # Group related segments
        grouped_segments = await group_related_segments(segments)

        # Initialize a list to hold all entities
        all_entities = []

        for group in grouped_segments:
            # Combine the segments in the group
            combined_text = " | ".join(group)

            # Extract entities from the combined text
            entity_result = await get_entities(combined_text)
            if entity_result:
                all_entities.append(entity_result["entities"])

        logger.info(f"Entities extracted from segments: {all_entities}")

    import asyncio
    asyncio.run(main())
