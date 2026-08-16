import streamlit as st
import pandas as pd
from PIL import Image
import io
import time
import gspread
from data.ingestion import init_connection
import logging

def compress_image(image_bytes, max_size=(800, 800), quality=80):
    img = Image.open(io.BytesIO(image_bytes))
    img.thumbnail(max_size)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality)
    return buffer.getvalue()

def save_to_sourcing_vault(sku, price, tags, image_url, std_price, vip_price, clr_price, stock_qty):
    """
    Appends a new cataloged item and custom pricing to the Sourcing_Vault tab.
    """
    try:
        # 1. Prepare clean GCP credentials  
        
        client_gspread = init_connection()
        
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

        # 3. Append the new item to the Sourcing_Vault
        sheet.append_row([sku, price, tags, image_url, std_price, vip_price, clr_price, stock_qty])
        return True
        
    except gspread.exceptions.SpreadsheetNotFound:
        st.error("Spreadsheet Not Found: Please ensure the Google Sheet is named exactly 'Jewelry Business DB' and shared with the Service Account.")
        return False
    except Exception as e:
        logging.error(f"Failed to update Google Sheet: {e}", exc_info=True)
        return False

def delete_from_sourcing_vault(sku):
    """
    Finds the specific SKU in the Sourcing_Vault tab and deletes the entire row.
    """
    try:
        client = init_connection()
        
        sheet_id = st.secrets.get("spreadsheet_id") or st.secrets.get("gcp_service_account", {}).get("spreadsheet_id")
        if sheet_id:
            try:
                sh = client.open_by_key(sheet_id)
            except Exception:
                sh = client.open("Jewelry Business DB")
        else:
            sh = client.open("Jewelry Business DB")
            
        sheet = sh.worksheet("Sourcing_Vault")
        
        # Search the entire sheet for the exact SKU string
        cell = sheet.find(sku)
        
        if cell:
            # Delete the specific row where the SKU was found
            sheet.delete_rows(cell.row)
            return True
        else:
            # If the SKU isn't found, it might have already been deleted manually
            return True 
            
    except Exception as e:
        logging.error(f"Google Sheets Deletion Failure: {e}", exc_info=True)
        return False