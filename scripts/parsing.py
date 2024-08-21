import ast
import logging

# Set up logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)

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
raw_data = """
[
    [
        ["Loan Agreement: A legal document between a lender and a borrower detailing the terms of a loan"],
        ["Property Deed: A legal document transferring ownership of a property"]
    ],
    [
        ["John Doe: Borrower: Loan Agreement, Property Deed"],
        ["123 Main St.: Property Address: Property Deed, Health Inspection Report, Loan Agreement"]
    ],
    ["Loan Underwriting", "Regulatory Compliance", "Property Transaction"],
    "These documents are related to a real estate transaction involving John Doe and the property located at 123 Main St."
]
"""

parsed_result = parse_response(raw_data)
print(parsed_result)
