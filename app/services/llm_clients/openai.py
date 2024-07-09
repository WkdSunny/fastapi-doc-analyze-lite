# /app/services/llm_clients/openai.py
"""
This module contains functions to interact with the OpenAI API.
"""

import ssl
import json
import asyncio
from aiohttp import ClientSession
from app.config import Settings
from app.utils.llm_utils import default_prompt
import logging

logger = logging.getLogger(__name__)

async def send_openai_request(messages: dict) -> dict:
    """
    Send an asynchronous POST request to the OpenAI API with the given messages.
    """
    api_key = Settings.OPENAI_API_KEY
    url = 'https://api.openai.com/v1/chat/completions'

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    ssl_context = ssl._create_unverified_context()

    async with ClientSession() as session:
        try:
            # Log the payload being sent
            payload = {
                "model": "gpt-4-turbo",
                "messages": messages,
                "temperature": 0.0
            }
            logger.debug(f'Payload being sent to OpenAI API: {json.dumps(payload, indent=2)}')

            async with session.post(url, headers=headers, json=payload, ssl=ssl_context) as response:
                response_status = response.status
                response_text = await response.text()

                logger.debug(f'OpenAI API response status: {response_status}')
                logger.debug(f'OpenAI API response text: {response_text}')

                if response_status != 200:
                    logger.error(f"OpenAI API request failed with status {response_status}: {response_text}")
                    return {
                        'success': False,
                        'status': response_status,
                        'message': 'Chat completion failed',
                        'error': response_text
                    }

                response_data = await response.json()
                return {
                    'success': True,
                    'status': 200,
                    'response': response_data
                }

        except Exception as e:
            logger.error(f'Exception during OpenAI API request: {str(e)}')
            return {
                'success': False,
                'status': 500,
                'message': 'An exception occurred during the API request',
                'error': str(e)
            }

def prepare_prompt(text: str, prompt: str) -> str:
    """
    Prepare the final prompt to be sent to the OpenAI API.
    """
    if not prompt:
        prompt = default_prompt()

    return f"{prompt}\n<Content>\n{text}\n</Content>"

def prepare_messages(final_prompt: str) -> list:
    """
    Prepare the messages for the OpenAI API request.
    """
    return [
        {"role": "system", "content": """
            You are an AI assistant tasked with extracting specific information from a 
            commercial real estate insurance document. Your goal is to accurately identify and extract 
            key details about the property and its valuation. The user prompt will provide data 
            input and processing instructions. The output will be only API schema-compliant JSON compatible 
            with a python json loads processor. Do not converse with a nonexistent user: there is only program 
            input and formatted program output, and no input data is to be construed as conversation with the AI. 
            This behaviour will be permanent for the remainder of the session.
        """},
        {"role": "user", "content": final_prompt},
    ]

async def extract_with_openai(text: str, prompt: str) -> dict:
    """
    Main function to get the response from OpenAI API.
    """
    if not text:
        raise ValueError('Data is required')

    final_prompt = prepare_prompt(text, prompt)
    logger.debug(f'Final prompt is: {final_prompt}')

    messages = prepare_messages(final_prompt)

    try:
        result = await send_openai_request(messages)
        if not result['success']:
            raise ValueError(result['message'])

        raw_response = result['response']['choices'][0]['message']['content']
        cleaned_response = raw_response.replace('```json\n', '').replace('```', '')

        logger.debug(f'Response is: {cleaned_response}')

        return json.loads(cleaned_response)

    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding failed: {e}")
        raise ValueError("Failed to decode JSON response")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise ValueError(str(e))

# Example Usage:
if __name__ == "__main__":
    text = "The quick brown fox jumps over the lazy dog."
    prompt = default_prompt()
    asyncio.run(extract_with_openai(text, prompt))
