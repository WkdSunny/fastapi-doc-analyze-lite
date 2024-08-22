import json
from typing import List, Dict, Any
from app.services.llm_clients.openai import send_openai_request
from app.models.rag_model import Segment, Classification
from app.utils.llm_utils import clean_prompt
from app.config import logger

async def extract_data(result: List[Dict[str, Any]], segments: List[Segment], classification: Classification) -> List[Dict[str, Any]]:
    """
    Extract data from the segments for further processing.
    """
    try:
        text_parts = []
        for i, r in enumerate(result):
            text_parts.append(f"Text from Document {i + 1}:\n{r['text']}\n")
        text = ''.join(text_parts)

        grouped_segments = []
        for segment in segments:
            seg = f"<Seg id='{segment.serial}'"
            if segment.relates_to:
                seg += f" rel_to='{segment.relates_to}'"
            if segment.relationship_type:
                seg += f" rel_type='{segment.relationship_type}'"
            seg += f">{segment.text}</Seg>"
            grouped_segments.append(seg)

        annotated_segments = '\n'.join(grouped_segments)

        system_prompt = (
            "You are an AI assistant specializing in extracting relevant information from documents. "
            "Your goal is to extract key information from the provided documents, ensuring that no important detail is overlooked. "
            "Ensure that the response is a properly formatted JSON object that can be parsed using json.loads() in Python."
            "Do not wrap the JSON response in code blocks or use backticks. "
            "Remember, this is a programmatic interaction, not a conversation with an AI."
        )

        user_prompt = (
            f"""
                Your task is to extract relevant information from the content provided below which has been extracted from multiple related files.
                The text inside the tags <classification> and </classification> contains the classification of the documents for understaing the context.

                <classification>
                **Document Information:** 
                {classification}
                </classification>

                **Segments:**
                {annotated_segments}

                INFORMATION FOR EXTRACTION:
                - Use the **Segments:** to extract information.
                - Text of segments may contain checkboxes or cross marks. If combined text of all segments contain:
                    -- A combination of checked, crossed, or blank boxes, consider checked as 'Yes', crossed as 'No', and blank as 'N/A'.
                    -- Pairs of boxes where some are checked and the rest are blank, consider checked as 'Yes' and blank as 'N/A'.
                    -- Pairs of boxes where some are crossed and the rest are blank, consider crossed as 'Yes' and blank as 'N/A'.
                - If there is a box with a 'Yes' or 'No' label to its left, either it is checked or crossed, 
                consider it as 'Yes' or 'No' depending on the closest label on the left.

                GOAL:
                - Use the information from **Document Information** to understand the context, purpose, and relationships among the documents.
                - Extract key information from **Segments** and **Text**.
                - Extract every granular detail from the documents.

                REQUIREMENTS:
                - Extract all details from the Segments.
                - Assume every segment may have some key information that needs to be extracted.
                - In case as key information is missing, make an educated guess based on the content. If not sure use N/A.
                - Double check for any comments, notes, or annotations provided in the documents.
                - Make sure to extract any list that is present in the documents.
                - Extract any checkboxes, cross marks, or tick marks in the documents and classify them.
                - Response format should be as flat as possible. Only seperated with section headers.
                
                DO NOT:
                - Do not include any other information apart from the extracted information in the response.
                - Do not include any part from the text inside <classification> tags in the extraction and response.
            """
        )

        message = [
            {"role": "system", "content": clean_prompt(system_prompt)},
            {"role": "user", "content": clean_prompt(user_prompt)}
        ]

        payload = {
            "messages": message,
            "model": "gpt-3.5-turbo",
            "max_tokens": 4096,
            "temperature": 0.0
        }

        raw_response = await send_openai_request(api_key=None, payload=payload, messages=message)
        logger.debug(f"Raw response from OpenAI: {raw_response}")

        if raw_response.get("success"):
            response = raw_response.get("response")
            if response:
                usage = response.get("usage")
                if "choices" in response and isinstance(response["choices"], list):
                    choice = response["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        data = choice["message"]["content"]
                        return {
                            "data": convert_to_json(data),
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
            logger.error(f"Failed to extract data: {response.get('error')}")
            return []

    except Exception as e:
        logger.error(f"Error extracting data: {e}")
        return []
    
def convert_to_json(data: List[Dict[str, Any]]) -> str:
    """
    Convert the extracted data to JSON format.
    """
    try:
        return json.loads(data)
    except Exception as e:
        logger.error(f"Error converting data to JSON: {e}")
        return data