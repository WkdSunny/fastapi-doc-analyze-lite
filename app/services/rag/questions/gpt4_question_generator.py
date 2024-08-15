# /app/services/gpt4_question_generator.py

import asyncio
from typing import List
from app.config import settings, logger
from app.services.llm_clients.openai import send_openai_request, prepare_messages

class GPT4QuestionGenerator:
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def generate_questions(self, keywords: List[str]) -> List[str]:
        """
        Generate questions using GPT-4 based on the given keywords.

        Args:
            keywords (List[str]): A list of keywords including entities, topics, and TF-IDF keywords.

        Returns:
            List[str]: A list of generated questions.
        """
        try:
            # Prepare the prompt
            prompt = f"Given the following keywords: {', '.join(keywords)}, generate relevant questions."

            # Prepare the messages
            messages = prepare_messages(system_prompt="You are a helpful assistant.", user_prompt=prompt)
            
            # Send the request using the reusable OpenAI service
            result = await send_openai_request(messages)
            
            if not result['success']:
                logger.error(f"OpenAI API request failed: {result['error']}")
                return []

            # Extract and return the questions from the response
            questions = [choice['message']['content'].strip() for choice in result['response']['choices']]
            return questions
        except Exception as e:
            logger.error(f"Error generating questions with GPT-4: {e}")
            raise

if __name__ == "__main__":
    async def test_gpt4_question_generator():
        question_generator = GPT4QuestionGenerator(api_key=settings.OPENAI_API_KEY)
        keywords = ["Apple Inc.", "iPhone", "Steve Jobs"]
        questions = await question_generator.generate_questions(keywords)
        logger.info(f"Generated Questions: {questions}")

    asyncio.run(test_gpt4_question_generator())
    