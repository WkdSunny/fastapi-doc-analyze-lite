#word.py

from docx import Document
import json

def useDocX(file_path):
    document = Document(file_path)
    paragraphs = [p.text for p in document.paragraphs]
    json_data = {
        'paragraphs': paragraphs
    }
    return json.dumps(json_data)