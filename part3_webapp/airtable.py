# part3_webapp/airtable.py

import os
import requests
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get Airtable credentials from environment variables
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")

def update_airtable(df):
    """
    Update Airtable with the processed data
    
    Args:
        df (pandas.DataFrame): The processed data
    """
    try:
        import os
        from pyairtable import Table
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv()
        
        # Get Airtable credentials
        api_key = os.getenv("AIRTABLE_API_KEY")
        base_id = os.getenv("AIRTABLE_BASE_ID")
        table_name = os.getenv("AIRTABLE_TABLE_NAME")
        
        if not all([api_key, base_id, table_name]):
            print("Airtable credentials not found in environment variables")
            return
        
        # Connect to Airtable
        table = Table(api_key, base_id, table_name)
        
        # Convert DataFrame to records
        records = df.to_dict(orient='records')
        
        # Batch create records (100 at a time to avoid API limits)
        batch_size = 10
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            formatted_batch = [{"fields": record} for record in batch]
            table.batch_create(formatted_batch)
            
        print(f"Successfully updated Airtable with {len(records)} records")
        
    except Exception as e:
        print(f"Error updating Airtable: {str(e)}")

def update_airtable(df):
    """
    Update Airtable with data from the DataFrame
    Returns a dictionary with status and any error messages
    """
    if not all([AIRTABLE_API_KEY, BASE_ID, TABLE_NAME]):
        return {"error": "Missing Airtable credentials in .env file"}
    
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    success_count = 0
    error_count = 0
    errors = []
    
    # Process in batches to avoid rate limits
    batch_size = 10
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]
        
        for _, row in batch.iterrows():
            # Clean the data - remove NaN values and convert to string
            clean_data = {}
            for key, value in row.items():
                if pd.notna(value):
                    # Limit field names to 100 characters (Airtable limit)
                    key_clean = str(key)[:100]
                    # Convert all values to string to avoid type issues
                    clean_data[key_clean] = str(value)
            
            data = {
                "fields": clean_data
            }
            
            try:
                response = requests.post(url, headers=headers, json=data)
                if response.status_code == 200 or response.status_code == 201:
                    success_count += 1
                else:
                    error_count += 1
                    error_msg = f"Error {response.status_code}"
                    try:
                        error_msg += f": {response.json().get('error', {}).get('message', '')}"
                    except:
                        error_msg += f": {response.text[:100]}"
                    errors.append(error_msg)
            except Exception as e:
                error_count += 1
                errors.append(f"Exception: {str(e)}")
    
    return {
        "success": success_count,
        "errors": error_count,
        "error_details": errors[:5] if errors else []  # Return first 5 errors only to avoid huge responses
    }
