# app/file_handler.py

import pandas as pd
import json

def load_data(file):
    if file.name.endswith('.csv'):
        return pd.read_csv(file)
    elif file.name.endswith('.xlsx'):
        return pd.read_excel(file, engine='openpyxl')
    elif file.name.endswith('.json'):
        content = file.read().decode('utf-8')
        data = json.loads(content)
        return pd.json_normalize(data)
    else:
        raise ValueError("Unsupported file format. Please upload CSV, Excel, or JSON.")
