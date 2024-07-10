# app/utils/llm_utils.py
"""
This module contains utility functions for the LLM service.
"""

def default_prompt ():
    prompt =  """
        Here is the details of the task:
        Task: Carefully read through the content and extract the following information -
        1. Loan Number
        2. Policy Number
        3. Effictive Date
        4. Expiration Date
        5. Name Insured
        6. Property Name
        7. Address
        8. City
        9. State
        10. Zip Code
        11. County
        12. Coverage Information Special: Usually found in notes. It can have additional declaration following after the item which can be in next few lines.
        13. Commercial Property Coverage Amount: This is a number after the text "Commercial Property Coverage Amount of Insurance" starting with $ (dollar) sign.
        14. Business Income: It is a Yes no field, if any preceeding value is found consider as Yes else No
        15. Business Income DED
        16. Terrorism Coverage
        17. Terrorism Specific Exclution
        18. Domestic Terrorism Excluded
        19. Replacement Cost
        20. Agreed Values
        21. Coisnsurance
        22. Equipment Breakdown
        22. Equipment Breakdown Amount
        23. Equipment Breakdown DED
        24. Earth Movement
        25. Earth Movement Coverage
        26. Earth Movement DED
        27. Commercial General Liability
        28. Commercial General Liability Per Occurrence Coverage
        29. Commercial General Liability General Aggregate Coverage
        30. Commercial General Liability Deductible
        31. Automobile Liability
        32. Umbrella Insurance Liability
        33. Umbrella Insurance Liability Each Occurrence
        34. Umbrella Insurance Liability Aggregate
        35. Flood Zone
        36. FLOOD HAZARD AREA
        37. Flood Insurer
        38. Flood Insurance Policy Number
        39. Flood Coverage/Limit
        40. Flood DED
        41. Comments/Notes/Remarks

        For each piece of information:
        - If explicitly stated in the document, extract it exactly as written.
        - For each item that is found return the the text that has been used to match the item in Matching Key.
        - If, for any item, the value is callucated using any given data, provide the formula used to calculate as the value in the Addl. Comments.
        - If, for any item, there is a specific condition to determine the value, provide the condition as the value in the Addl. Comments.
        - For Point 13. There can also be some additional % (percentage) added to it. If yes then calculate it.
        - For point 41. Pick any or all available comments and merge them with newline under point 41. Comments/Notes/Remarks. Don't exclude anything even if some part of the comment has already been used in any other item. But don't use comment from Flood Certificate.
        - If any information can be calculated from given data, perform the calculation and provide the result.
        - If not found or cannot be determined, use "N/A" as the value.
        - If 36. Flood Hazard Area not found check 35. Flood Zone. If the value of 35. Flood Zone contains alpbhabet either A or V, value of 36. Flood Hazard Area should be Yes else No.
        - Consider "Coverage" and "Limit" as synonames. So if an item has Coverage or Limit written and you get a value, usually number and can be prefixed with $ (dollar) after the word Limit or Coverage consider it as the Coverage for the item found at the begining or near to begining of the line
        - Most of the items starting from 13 to 26 usually has a DED or Deduction item. DED and Deduction both are same. Consider that as a part of DED of that section and add them to the respective DED items, like "15. Business Income DED", "23. Equipment Breakdown DED", "26. Earth Movement DED", "40. Flood DED", etc.

        Organize the data into a table with the following headers:
        Information Key | Matching Key | Matching Value | Value | Addl. Comments
        # And final output should be a JSON of that table as array of objects.
        Final Output should be csv of that table.
        # {
        #     "data": [
        #         {
        #             "key": "Loan Number",
        #             "matching_key": "Loan Number",
        #             "matching_value": "100001168",
        #             "value": "100001168",
        #             "additional_comments": "Another comment."
        #         },
        #         {
        #             "key": "Policy Number",
        #             "matching_key": "Policy Number",
        #             "matching_value": "97-B8-5008-1",
        #             "value": "97-B8-5008-1",
        #             "additional_comments": "This is a comment."
        #         }
        #     ]
        # }

        Here is the content of various insurance documents to analyze:
    """
    # Strip leading and trailing whitespaces from each line
    prompt = "\n".join(line.strip() for line in prompt.split("\n"))
    return prompt

# Example Usage:
if __name__ == "__main__":
    print(default_prompt())