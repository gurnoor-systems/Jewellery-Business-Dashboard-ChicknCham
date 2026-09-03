import streamlit as st
import pandas as pd
import gspread
import time
from oauth2client.service_account import ServiceAccountCredentials
from data.security import decrypt_pii

@st.cache_resource
def init_connection():
    """Authenticates and caches the ENTIRE workbook to save API calls."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)
    
    sheet_id = st.secrets.get("spreadsheet_id") or st.secrets.get("gcp_service_account", {}).get("spreadsheet_id")
    if sheet_id:
        return client.open_by_key(sheet_id)
        
    return client.open("Jewelry Business DB")

def fetch_with_retry(worksheet_name, max_retries=3):
    """Fetches data from Google Sheets with Exponential Backoff for 503/429 errors."""
    for attempt in range(max_retries):
        try:
            db = init_connection()
            return pd.DataFrame(db.worksheet(worksheet_name).get_all_records())
        except Exception as e:
            if "503" in str(e) or "429" in str(e) or "APIError" in str(e):
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Waits 1s, then 2s, then 4s
                    continue
            raise e

@st.cache_data(ttl=600) 
def load_data():
    # Use the new robust fetcher
    df_sales = fetch_with_retry("Sales_Engine")
    df_sourcing = fetch_with_retry("Sourcing_Vault")
    
    if not df_sales.empty:
        df_sales.columns = df_sales.columns.str.strip()
        
        if 'Client Formal Name' in df_sales.columns:
            df_sales['Client Formal Name'] = df_sales['Client Formal Name'].apply(decrypt_pii)
        if 'Instagram/Facebook Handle' in df_sales.columns:
            df_sales['Instagram/Facebook Handle'] = df_sales['Instagram/Facebook Handle'].apply(decrypt_pii)
            
        if 'Date of Sale' in df_sales.columns:
            df_sales['Date of Sale'] = pd.to_datetime(df_sales['Date of Sale'], errors='coerce')

    if not df_sourcing.empty:
        df_sourcing.columns = df_sourcing.columns.str.strip()
        if 'Date of Purchase' in df_sourcing.columns:
            df_sourcing['Date of Purchase'] = pd.to_datetime(df_sourcing['Date of Purchase'], errors='coerce')
            
    return df_sales, df_sourcing

@st.cache_data(ttl=600)
def load_sourcing_vault():
    """Fallback function using the robust fetcher."""
    return fetch_with_retry("Sourcing_Vault")