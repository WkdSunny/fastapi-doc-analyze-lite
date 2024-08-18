import csv
from io import StringIO
from typing import List, Dict
from app.utils.date_utils import convert_to_iso_date

async def parse_csv_content(
    csv_content: str, 
    delimiter: str = "|", 
    quotechar: str = '"',
    has_header: bool = True
) -> List[Dict[str, str]]:
    """
    Parse the CSV content into a list of dictionaries.

    Args:
        csv_content (str): The content of the CSV file.
        delimiter (str): The delimiter used in the CSV file. Defaults to "|".
        quotechar (str): The character used to quote fields. Defaults to '"'.
        has_header (bool): Whether the CSV file contains a header row. Defaults to True.

    Returns:
        List[Dict[str, str]]: A list of dictionaries where each dictionary represents a row in the CSV file.
    """
    try:
        f = StringIO(csv_content)
        reader = csv.reader(f, delimiter=delimiter, quotechar=quotechar)

        parsed_data = []

        if has_header:
            headers = [header.strip().lower() for header in next(reader)]  # Use the first row as headers
        else:
            first_row = next(reader)
            headers = [f"column_{i+1}" for i in range(len(first_row))]
            parsed_data.append(dict(zip(headers, first_row)))

        for row in reader:
            converted_row = {header: await convert_to_iso_date(value.strip()) for header, value in zip(headers, row)}
            parsed_data.append(converted_row)

        return parsed_data

    except csv.Error as e:
        raise ValueError(f"Error parsing CSV content: {e}")
    except Exception as e:
        raise ValueError(f"Unexpected error parsing CSV content: {e}")

# Example usage:
if __name__ == "__main__":
    import asyncio
    
    csv_content = """
        Category|Entity
        Organization|DEPARTMENT OF HOMELAND SECURITY
        Organization|FEDERAL EMERGENCY MANAGEMENT AGENCY
        Organization|JPMORGAN CHASE BANK, N.A. CTL
        Person|CHETAN RAMAIAH
        Person|SANFORD K. MA
        Person|GLORIA F. MA
        Location|FORT WORTH, TX
        Location|OAKLAND, CA
        Location|ALAMEDA COUNTY
        Location|ARLINGTON, TX
        Date|May 30, 2015
        Date|August 03, 2009
        Date|December 17, 2015
        Identifier|O.M.B. No. 1660-0040
        Identifier|1000205654
        Identifier|008-0631-006-01
        Identifier|100001168
        Identifier|065048
        Identifier|06001C0067G
        Identifier|2105924329
        Miscellaneous|SFHDF
        Miscellaneous|FEMA Bulletin W-14022
        Miscellaneous|NFIP
        Miscellaneous|HMDA Information
        Miscellaneous|CBRA
        Miscellaneous|OPA
    """

    # Test without a header
    csv_content_no_header = """
        Organization|DEPARTMENT OF HOMELAND SECURITY
        Organization|FEDERAL EMERGENCY MANAGEMENT AGENCY
        Organization|JPMORGAN CHASE BANK, N.A. CTL
        Person|CHETAN RAMAIAH
        Person|SANFORD K. MA
        Person|GLORIA F. MA
    """

    async def main():
        parsed_data = await parse_csv_content(csv_content)
        print(parsed_data)

        parsed_data_no_header = await parse_csv_content(csv_content_no_header, has_header=False)
        print(parsed_data_no_header)

    # Run the main function
    asyncio.run(main())
