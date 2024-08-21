from typing import List
from app.services.llm_clients.openai import send_openai_request
from app.models.rag_model import Classification
from app.utils.llm_utils import clean_prompt
from app.utils.csv_utils import parse_csv_content
from app.config import logger

async def classify_documents(text: str, content_type: str) -> List[Classification]:
    try:
        mime_type = content_type.split("/")[1]
        system_prompt = (
            "You are an AI that specializes in document classification. "
            "You will be given a text that has been extracted from a document. "
            "You are asked to Identify the category or type of document accurately. "
            "Your goal is to accurately identify, categorize and add a brief description about the text. "
            "Remember, this is a programmatic interaction, not a conversation with an AI."
        )

        user_prompt = (f"""
            The text below, enclosed in <text> tags, is extracted from a {mime_type} file.

            <text>
            {text}
            </text>

            Requirements:
                1. Classify the document based on the text.
                2. Add a brief description of the document's likely use.
                3. Return the result in the following CSV format: classification|description
                4. Use a pipe '|' as the delimiter.

            Example:
            classification|description
            Invoice|This is an invoice for the purchase of goods.
        """
        )

        message = [
            {"role": "system", "content": clean_prompt(system_prompt)},
            {"role": "user", "content": clean_prompt(user_prompt)}
        ]

        payload = {
            "model": "gpt-4-turbo",
            "messages": message,
            "max_tokens": 100,
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
                        classification = choice["message"]["content"]
                        classication_dict = await parse_csv_content(classification)
                        logger.debug(f"Classification: {classication_dict}")
                        return {
                            "classification": classication_dict,
                            "usage": usage
                        }
                    else:
                            logger.error(f"'message' or 'content' key not found in the response choice: {choice}")
                else:
                    logger.error(f"'choices' key not found or not a list in the response: {response}")
            else:
                logger.error("No 'response' found in raw_response.")
        else:
            # Log the error message from the response
            logger.error(f"Failed to classify: {response.get('error')}")
            return None
    except Exception as e:
        logger.error(f"Error classifying document: {e}")
        return None