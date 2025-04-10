# part3_webapp/airtable.py banana padega agar chahiye

import os
import requests

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = "your_base_id"
TABLE_NAME = "your_table_name"

def update_airtable(df):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }

    for _, row in df.iterrows():
        data = {
            "fields": row.to_dict()
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200:
            print("Failed to upload:", response.json())
