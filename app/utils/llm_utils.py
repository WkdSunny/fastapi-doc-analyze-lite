# app/utils/llm_utils.py
"""
This module contains utility functions for the LLM service.
"""

def default_prompt ():
    return """
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
        - For Point 13. There can also be some additional % (percentage) added to it. If yes then calculate it.
        - For point 41. Pick any or all available comments and merge them with newline under point 41. Comments/Notes/Remarks. Don't exclude anything even if some part of the comment has already been used in any other item.
        - If any information can be calculated from given data, perform the calculation and provide the result.
        - If not found or cannot be determined, use "N/A" as the value.
        - If 36. Flood Hazard Area not found check 35. Flood Zone. If the value of 35. Flood Zone contains alpbhabet either A or V, value of 36. Flood Hazard Area should be Yes else No.
        - Consider "Coverage" and "Limit" as synomames. So if an item has Coverage or Limit written and you get a value, usually number and can be prefixed with $ (dollar) after the word Limit or Coverage consider it as the Coverage for the item found at the begining or near to begining of the line
        - Most of the items starting from 13 to 26 usually has a DED or Deduction item. DED and Deduction both are same. Consider that as a part of DED of that section and add them to the respective DED items, like "15. Business Income DED", "23. Equipment Breakdown DED", "26. Earth Movement DED", "40. Flood DED", etc.

        Organize the data into a table with the following headers:
        Information Key | Value
        And final output should be a JSON of that table as array of objects.

        Here is the content of various insurance documents to analyze:
    """

# Example Usage:
if __name__ == "__main__":
    print(default_prompt())