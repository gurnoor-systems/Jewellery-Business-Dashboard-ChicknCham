import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from data.security import decrypt_pii

@st.cache_resource
def init_connection():
    """Authenticates and caches the ENTIRE workbook to save API calls."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    # Open and cache the database once globally
    return gspread.authorize(creds).open("Jewelry Business DB")

@st.cache_data(ttl=600) 
def load_data():
    db = init_connection()
    
    df_sales = pd.DataFrame(db.worksheet("Sales_Engine").get_all_records())
    df_sourcing = pd.DataFrame(db.worksheet("Sourcing_Vault").get_all_records())
    
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
    """Fallback function tapping into the cached workbook."""
    return pd.DataFrame(init_connection().worksheet("Sourcing_Vault").get_all_records())