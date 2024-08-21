from typing import List, Dict
from collections import defaultdict
from app.services.llm_clients.openai import send_openai_request
from app.models.rag_model import Segment, Classification, Entity, Topic, TFIDFKeyword
from app.utils.llm_utils import clean_prompt
from app.config import logger

async def generate_questions(
        segments: List[Segment],
        classification: str, 
        entities: List[Entity], 
        topics: List[Topic],
        keywords: List[TFIDFKeyword]
    ) -> List[str]:
    try:
        def grouped_entities(entities: List[Entity]) -> Dict[str, List[str]]:
            """
            Group questions based on their type.
            """
            grouped_entities = defaultdict(list)
            for entity in entities:
                logger.debug(f"Entity: {entity}")
                grouped_entities[entity.entity].append(entity)

            logger.debug(f"Grouped entities: {grouped_entities}")

            entity_text = ""
            for entity_type, entity_list in grouped_entities.items():
                entity_text += f"*{entity_type}*\n"

                for entity in entity_list:
                    entity_text += f"- {entity.text}: {entity.description}\n"
                    entity_text += f"Entity is related to segment {entity.segment_serial}\n"
                    entity_text += f"\n"

            logger.info(f"Entity text: {entity_text}")
            return entity_text
        
        system_prompt = (
            "You are an AI assistant specializing in generating detailed and specific questions from document content. "
            "Your goal is to create distinct, granular questions based on the provided documents, ensuring that no concept is left unexamined."
            "Remember, this is a programmatic interaction, not a conversation with an AI."
        )

        user_prompt = (
            f"""
            Your task is to generate a comprehensive list of questions based on the content below that has been extracted from multiple related files.
            Entire content of the file has been enclosed in <content> tags.

            <content>
            **Document Information:** 
            {classification}

            **Entities:**
            {grouped_entities(entities)}

            **Topics:**
            {', '.join([' '.join(topic.words) for topic in topics])}

            **Keywords:**
            {', '.join([keyword for keyword in keywords])}

            **Document Segments:**
            {''.join(
                [
                    f"""
                    {segment.serial}. {segment.text}\n
                    *Relates to*: Segment {segment.relates_to} ({segment.relationship_type})\n
                    """ 
                    for segment in segments if segment.relates_to is not None  # Filter to include only relevant relationships
                ]
            )}
            </content>

            Information for AI:
            - The questions you generate will be used to extract specific details from the document content.
            - If you miss any aspect and a question is not generated, that information may be lost.
            - Carefully analyze the content and details, including classifications, entities, topics, keywords, and relationships between entities.
            - Revalidate the generated questions against the segments and entities to ensure all details are covered.


            Requirements:
            1. Generate a comprehensive list of distinct questions relevant to the document content, covering every aspect of the document.
            2. For each classification, entity, topic, and keyword, generate multiple questions to ensure all possible details are captured.
            3. Ensure each question focuses on extracting specific details rather than broad concepts.
            4. Avoid merging related concepts into a single question; instead, create separate questions for each detail.
            5. Consider relationships between entities and generate questions that explore these connections in depth.
            6. Return the questions as a list of strings, ensuring the response format is as detailed as possible.

            Example Response Format:
                What is the document classified as?
                What are the entities mentioned in the document?
                What are the topics covered in the document?
                What are the keywords extracted from the document?
            """
        )

        messages = [
            {"role": "system", "content": clean_prompt(system_prompt)},
            {"role": "user", "content": clean_prompt(user_prompt)}
        ]

        payload = {
            "model": "gpt-3.5-turbo",
            "messages": messages,
            "max_tokens": 2500,
            "temperature": 0.0
        }

        raw_response = await send_openai_request(api_key=None, payload=payload, messages=messages)
        logger.debug(f"Raw response: {raw_response}")

        if raw_response.get("success"):
            response = raw_response.get("response")
            if response:
                usage = response.get("usage")
                if "choices" in response and isinstance(response["choices"], list):
                    choice = response["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        questions = choice["message"]["content"].split("\n")
                        logger.info(f"Generated questions: {questions}")
                        return {
                            "questions": questions,
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
            logger.error(f"Failed to generate questions: {response.get('error')}")
            return None
    except Exception as e:
        logger.error(f"An error occurred while generating questions: {e}")
        return None
    