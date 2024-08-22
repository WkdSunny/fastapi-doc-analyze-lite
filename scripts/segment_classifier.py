import spacy
import re

nlp = spacy.load("en_core_web_lg")

def extract_tables(text):
    # Simple heuristic to detect tables based on patterns like row structures
    table_pattern = re.compile(r"(\w+\s+\d+\s+\w+)|(\d+\s+\d+\s+\d+)", re.MULTILINE)
    tables = []
    for match in re.finditer(table_pattern, text):
        table_start = match.start()
        table_end = text.find("\n\n", table_start)
        if table_end == -1:
            table_end = len(text)
        table_text = text[table_start:table_end].strip()
        if len(table_text.splitlines()) > 1:
            rows = [row.split() for row in table_text.splitlines()]
            tables.append({"caption": "", "rows": rows})
    return tables

def extract_figures(text):
    # Simple heuristic for figures based on common patterns like "Figure X: ..."
    figure_pattern = re.compile(r"Figure\s+\d+:\s*(.*)", re.IGNORECASE)
    figures = []
    for match in re.finditer(figure_pattern, text):
        figure_caption = match.group(1).strip()
        figures.append({"caption": figure_caption})
    return figures

def extract_lists(text):
    # Simple heuristic for lists based on patterns like bullets or numbering
    list_pattern = re.compile(r"^\s*[\d\-\*\+]\s*(.*)", re.MULTILINE)
    lists = []
    current_list = []
    for match in re.finditer(list_pattern, text):
        item = match.group(1).strip()
        current_list.append(item)
    if current_list:
        lists.append(current_list)
    return lists

def classify_text(text):
    doc = nlp(text)
    # Initialize the result structure
    result = {
        "text": "",
        "tables": [],
        "figures": [],
        "lists": []
    }
    
    # Segment text and classify
    paragraphs = text.split("\n\n")
    for para in paragraphs:
        if re.search(r"\btable\b", para, re.IGNORECASE):
            result["tables"].extend(extract_tables(para))
        elif re.search(r"\bfigure\b", para, re.IGNORECASE):
            result["figures"].extend(extract_figures(para))
        elif re.search(r"^\s*[\d\-\*\+]\s", para, re.MULTILINE):
            result["lists"].extend(extract_lists(para))
        else:
            result["text"] += para + "\n\n"
    
    # Clean up text
    result["text"] = result["text"].strip()
    
    return result

# Example usage
document_text = """
Introduction to sustainable energy. This is a sample document. It contains multiple sentences. Each sentence is a segment. However, there are some differences.

1. Solar energy
2. Wind energy
3. Hydroelectric energy

Figure 1: Growth of Renewable Energy Sources.

Energy Investments by Year
Year    Solar   Wind    Hydro
2020    100MW   150MW   200MW
2021    110MW   160MW   210MW
"""

classified_data = classify_text(document_text)
print(classified_data)
