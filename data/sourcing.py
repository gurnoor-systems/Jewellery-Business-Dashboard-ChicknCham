import streamlit as st
import pandas as pd
from PIL import Image
import io
import time
import gspread

def compress_image(image_bytes, max_size=(800, 800), quality=80):
    img = Image.open(io.BytesIO(image_bytes))
    img.thumbnail(max_size)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality)
    return buffer.getvalue()

def save_to_sourcing_vault(sku, price, tags, image_url):
    """
    Appends a new cataloged item to the 'Sourcing_Vault' tab in Google Sheets.
    """
    try:
        # 1. Prepare clean GCP credentials
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds_dict.pop("spreadsheet_id", None)  
        
        client_gspread = gspread.service_account_from_dict(creds_dict)
        
        # 2. Retrieve spreadsheet_id safely from secrets
        sheet_id = st.secrets.get("spreadsheet_id") or st.secrets.get("gcp_service_account", {}).get("spreadsheet_id")
        
        if sheet_id:
            try:
                sh = client_gspread.open_by_key(sheet_id)
            except Exception:
                # Fallback if ID is incorrect
                sh = client_gspread.open("Jewelry Business DB")
        else:
            # Fallback to opening by exact spreadsheet title
            sh = client_gspread.open("Jewelry Business DB")
            
        sheet = sh.worksheet("Sourcing_Vault")
        sheet.append_row([sku, price, tags, image_url])
        return True
        
    except gspread.exceptions.SpreadsheetNotFound:
        st.error("Spreadsheet Not Found: Please ensure the Google Sheet is named exactly 'Jewelry Business DB' and shared with the Service Account.")
        return False
    except Exception as e:
        st.error(f"Failed to update Google Sheet: {e}")
        return False