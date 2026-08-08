import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

@st.cache_resource
def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

@st.cache_data(ttl=600) 
def load_data():
    client = init_connection()
    sheet = client.open("Jewelry Business DB")
    
    df_sales = pd.DataFrame(sheet.worksheet("Sales_Engine").get_all_records())
    df_sourcing = pd.DataFrame(sheet.worksheet("Sourcing_Engine").get_all_records())
    
    # DEFENSE 1: Check for empty database
    if df_sales.empty or df_sourcing.empty:
        return df_sales, df_sourcing
        
    # DEFENSE 2: Strip invisible trailing spaces
    df_sales.columns = df_sales.columns.str.strip()
    df_sourcing.columns = df_sourcing.columns.str.strip()
    
    # DEFENSE 3: Format dates safely
    if 'Date of Sale' in df_sales.columns:
        df_sales['Date of Sale'] = pd.to_datetime(df_sales['Date of Sale'], errors='coerce')
    else:
        raise KeyError(f"Could not find 'Date of Sale'. Columns found: {list(df_sales.columns)}")
        
    if 'Date of Purchase' in df_sourcing.columns:
        df_sourcing['Date of Purchase'] = pd.to_datetime(df_sourcing['Date of Purchase'], errors='coerce')
        
    return df_sales, df_sourcing