#excel.py

import openpyxl
import json

def useOpenPyXL(file_path):
    workbook = openpyxl.load_workbook(file_path)
    worksheet = workbook.active

    data = []
    for row in worksheet.iter_rows(values_only=True):
        data.append(row)

    headers = data[0]
    json_data = []
    for row in data[1:]:
        json_row = {}
        for i, value in enumerate(row):
            json_row[headers[i]] = value
        json_data.append(json_row)

    return json.dumps(json_data)