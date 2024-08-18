# /app/services/llm_clients/openai.py
"""
This module contains functions to interact with the OpenAI API.
"""

import ssl
import json
import asyncio
from aiohttp import ClientSession
from typing import Dict, Any, Optional
from app.config import Settings, logger
from app.utils.llm_utils import default_system_prompt, default_user_prompt

async def send_openai_request(api_key: Optional[str], messages: Dict[str, Any], payload: Optional[Dict[str, Any]]) -> dict:
    """
    Send an asynchronous POST request to the OpenAI API with the given messages.
    """
    if not api_key:
        api_key = Settings.OPENAI_API_KEY
    url = 'https://api.openai.com/v1/chat/completions'

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    ssl_context = ssl._create_unverified_context()

    async with ClientSession() as session:
        try:
            if not payload:
                payload = {
                    "model": "gpt-3.5-turbo",
                    "messages": messages,
                    "max_tokens": 1000,
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

def prepare_messages(system_prompt: str, user_prompt: str) -> list:
    """
    Prepare the messages for the OpenAI API request.
    """
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
# Example usage
if __name__ == "__main__":
    messages = [
        {"role": "system", "content": default_system_prompt},
        {"role": "user", "content": default_user_prompt}
    ]
    asyncio.run(send_openai_request(api_key=None, messages=messages, payload=None))