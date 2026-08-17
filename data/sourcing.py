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

def batch_deduct_inventory(cart_items):
    """
    Deducts stock for a batch of SKUs in a single Google Sheets API call.
    Expects cart_items as a list of dicts: [{'sku': 'JK-123...', 'qty': 2}, ...]
    """
    if not cart_items:
        return True

    try:
        # Securely connect to the database
        client = init_connection()
        sheet_id = st.secrets.get("spreadsheet_id") or st.secrets.get("gcp_service_account", {}).get("spreadsheet_id")
        sh = client.open_by_key(sheet_id) if sheet_id else client.open("Jewelry Business DB")
        sheet = sh.worksheet("Sourcing_Vault")

        # 1. Fetch current database state
        all_data = sheet.get_all_records()
        headers = sheet.row_values(1)
        
        # Ensure the column actually exists to prevent crashes
        if "Stock_Quantity" not in headers:
            logging.error("Column 'Stock_Quantity' missing in Sourcing_Vault.")
            return False
            
        col_idx = headers.index("Stock_Quantity") + 1
        updates = []

        # 2. Match SKUs and calculate safe deductions
        for idx, row in enumerate(all_data):
            sku = str(row.get("Item_SKU", "")).strip()
            
            for item in cart_items:
                if item['sku'] == sku:
                    try:
                        sold_qty = int(item['qty'])
                        # Handle empty cells safely
                        current_stock = row.get("Stock_Quantity", 0)
                        current_stock = int(current_stock) if str(current_stock).strip() != "" else 0
                    except ValueError:
                        continue
                        
                    # 🚀 The Oversell Protection (The Floor)
                    new_stock = max(0, current_stock - sold_qty)
                    
                    # Row index is idx + 2 (1 for header, 1 because gspread is 1-indexed)
                    row_idx = idx + 2 
                    
                    # Prepare the A1 notation cell target (e.g., 'H4')
                    cell_target = gspread.utils.rowcol_to_a1(row_idx, col_idx)
                    
                    updates.append({
                        'range': cell_target,
                        'values': [[new_stock]]
                    })
                    break # Move to next database row once matched

        # 3. Execute the single batch update payload
        if updates:
            sheet.batch_update(updates)
            
        return True
        
    except Exception as e:
        logging.error(f"Batch Inventory Deduct Failure: {e}", exc_info=True)
        return False