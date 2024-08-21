import ast
from typing import List, Dict, Any
from app.services.llm_clients.openai import send_openai_request
from app.models.rag_model import Classification
from app.utils.llm_utils import clean_prompt
from app.utils.csv_utils import parse_csv_content
from app.config import logger

async def classify_documents(result: Dict[str, Any]) -> List[Classification]:
    try:
        text = grouped_text(result)
        if not text:
            logger.error("No text found in the result.")
            raise ValueError("No text found in the result.")

        system_prompt = (
            "You are an AI assistant specialized in document analysis and relationship extraction. "
            "You will be provided with text extracted from multiple related documents. "
            "Your goal is to accurately complete the specified tasks in the user prompt. "
            "Remember, this is a programmatic interaction, not a conversation with an AI."
        )

        user_prompt = (f"""
            TASKS:
            1. Identify the types of documents from the data provided.
            2. Establish the relationship among these documents by identifying common entities, connections, and references.
            3. Determine the overall purpose or use of this data as a whole.
                       
            EXTRACTED TEXT:
            {text}
            
            INSTRUCTIONS:
            Step 1: Identify the type of each document, providing a brief description of what the document is.
            Step 2: Identify relationships among the documents including but not limited to:
                - Any common entities (e.g., individuals, organizations, addresses).
                - Shared references (e.g., loan numbers, insurance policies).
                - How these documents are connected.
            Step 3: Summarize the overall use of these documents:
                - Explain how they are used together in a specific process: (e.g., loan underwriting, regulatory compliance)
                - What is the purpose of this combined data might be.
            Step 4: Below is am example of the format you will use to return the data.

            EXAMPLE RESPONSE FORMAT:
            Document Types and Descriptions:
            Loan Agreement: A legal document between a lender and a borrower detailing the terms of a loan
            Property Deed: A legal document transferring ownership of a property

            Relationships:
            Swiss Bank: Borrowers mentioned in Land Agreement and Property Deed
            1234 Boulevard Avenue, Oakland, CA: Property address shared in Property Deed, Loan Agreement and Health Inspection Report
            Uuid 10000101: Referenced in Loan Agreement and Property Deed
            
            Document Usage:
            Loan Underwriting
            Insurance Coverage Verification
            Property Risk Assessment

            Summary:
            These documents are related to evaluating risk, verifying insurance coverage, and assessing the financial requirements for a property located at a specific address. The documents collectively provide important information needed for risk management and compliance.
        """
        )

        message = [
            {"role": "system", "content": clean_prompt(system_prompt)},
            {"role": "user", "content": clean_prompt(user_prompt)}
        ]

        payload = {
            "model": "gpt-3.5-turbo",
            "messages": message,
            "max_tokens": 500,
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
                        # classication_dict = await parse_csv_content(classification)
                        # logger.debug(f"Classification: {classication_dict}")
                        # return {
                        #     "classification": classication_dict,
                        #     "usage": usage
                        # }
                        return {
                            "classification": classification,
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
            logger.error(f"Failed to classify: {response.get('error')}")
            return None
    except Exception as e:
        logger.error(f"Error classifying document: {e}")
        return None
    
def grouped_text(result: List[Dict[str, Any]]) -> List[str]:
    try:
        logger.debug(f"Result is: {result}")
        grouped_sections = []
        for i, r in enumerate(result):
            i += 1
            section = f"**Text from Document {i}**\n{r['text']}"
            grouped_sections.append(section)

        return grouped_sections
    except Exception as e:
        logger.error(f"Error grouping text: {e}")
        return None
    
import ast

def parse_response(data: str):
    try:
        # Convert the raw string into a Python list using ast.literal_eval for safety
        data = ast.literal_eval(data)
        logger.debug(f"Converted Data: {data}")

        document_types = []
        for doc_list in data[0]:
            doc = doc_list[0]
            logger.debug(f"Current Document: {doc}")
            doc_type, doc_desc = doc.split(":", 1)
            document_types.append({
                "document_type": doc_type.strip(),
                "description": doc_desc.strip()
            })

        relationships = []
        for rel_list in data[1]:
            rel = rel_list[0]
            entity, role, related_to = rel.split(":", 2)
            relationships.append({
                "entity": entity.strip(),
                "relationship": role.strip(),
                "related_entities": [e.strip() for e in related_to.split(",")]
            })

        # Combine all into a single JSON-like dictionary
        result = {
            "document_types": document_types,
            "relationships": relationships,
            "document_usage": data[2],
            "summary": data[3]
        }
        logger.debug(f"Final Parsed Result: {result}")

        return result

    except Exception as e:
        logger.error(f"Error parsing classification response: {e}")
        return None

# Example usage with the provided raw string
# raw_data = """
# [
#     [
#         ["Standard Flood Hazard Determination Form (SFHDF): A form used by FEMA to determine flood hazard areas and insurance requirements"],
#         ["Evidence of Commercial Property Insurance: A document providing evidence of insurance coverage for commercial property"],
#         ["Certificate of Liability Insurance: A certificate providing information on liability insurance coverage"]
#     ],
#     [
#         ["entity: Sanford K. Ma and Gloria F. Ma", "role: Borrower", "related_to: SFHDF, Evidence of Commercial Property Insurance"],
#         ["entity: 1445 Lakeside Dr, Oakland, CA", "role: Property Address", "related_to: SFHDF, Evidence of Commercial Property Insurance, Certificate of Liability Insurance"],
#         ["entity: JPMorgan Chase Bank, N.A.", "role: Lender", "related_to: SFHDF, Evidence of Commercial Property Insurance, Certificate of Liability Insurance"]
#     ],
#     ["Loan Underwriting", "Insurance Coverage Verification", "Risk Management"],
#     "These documents are related to a real estate transaction involving Sanford K. Ma and Gloria F. Ma as borrowers, with JPMorgan Chase Bank, N.A. as the lender. They are used for loan underwriting, insurance coverage verification, and risk management purposes."
# ]
# """

# parsed_result = parse_response(raw_data)
# print(parsed_result)
