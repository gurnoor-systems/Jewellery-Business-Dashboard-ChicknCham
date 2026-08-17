import streamlit as st
import gspread
import pandas as pd
from datetime import datetime
import pytz
from data.ingestion import init_connection
from data.security import encrypt_pii
from data.sourcing import batch_deduct_inventory
import logging

def log_new_sale(formal_name, handle, line_items_df, total_pieces, total_cost, courier, amount_paid, payment_status):

    # Inside log_new_sale function, encrypt before sending to Google Sheets:
    secure_handle = encrypt_pii(handle)
    secure_name = encrypt_pii(formal_name)
    """
    Serializes the POS cart to JSON and logs the transaction to the Sales_Engine tab.
    """
    try:
        # 1. Establish Secure Database Connection
        
        client_gspread = init_connection()
        sheet_id = st.secrets.get("spreadsheet_id") or st.secrets.get("gcp_service_account", {}).get("spreadsheet_id")
        
        if sheet_id:
            try:
                sh = client_gspread.open_by_key(sheet_id)
            except Exception:
                sh = client_gspread.open("Jewelry Business DB")
        else:
            sh = client_gspread.open("Jewelry Business DB")
            
        sheet = sh.worksheet("Sales_Engine")
        
        # 2. Serialize the Dynamic Cart to JSON
        # This solves the pie chart and invoice parsing problem
        line_items_json = line_items_df.to_json(orient="records")
        
        # 3. Generate Localized Timestamps (IST for Delhi)
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)
        timestamp_str = current_time.strftime("%d/%m/%Y %H:%M:%S")
        date_str = current_time.strftime("%B %d, %Y")
        
        # 4. Map Data to Columns A through J
        row_data = [
            timestamp_str,       # A: Timestamp
            date_str,            # B: Date of Sale
            formal_name,         # C: Client Formal Name
            handle,              # D: Instagram/Facebook Handle
            line_items_json,     # E: Line_Items_JSON
            total_pieces,        # F: Total Pieces Sold
            total_cost,          # G: Total Cost of These Items
            courier,             # H: Courier Charge You Paid
            amount_paid,         # I: Amount Client Paid
            payment_status       # J: Payment Status
        ]
        
        # 5. Execute Database Write
        sheet.append_row(row_data)
        
        # 6. LIVE INVENTORY DEDUCTION
        try:
            vault_sheet = sh.worksheet("Sourcing_Vault")
            
            for index, row in line_items_df.iterrows():
                sku = str(row.get("Item_SKU", "")).strip()
                qty_sold = int(row.get("Quantity", 0))
                
                # Only attempt deduction if an SKU was provided
                if sku and qty_sold > 0:
                    # Find the exact row matching the SKU in Column A
                    cell = vault_sheet.find(sku, in_column=1)
                    if cell:
                        # Fetch current stock from Column H (Column 8)
                        stock_cell_val = vault_sheet.cell(cell.row, 8).value
                        current_stock = int(stock_cell_val) if stock_cell_val else 0
                        
                        # Calculate new stock (prevents negative numbers)
                        new_stock = max(0, current_stock - qty_sold)
                        
                        # Write the new stock integer back to the database
                        vault_sheet.update_cell(cell.row, 8, new_stock)
        except Exception as e:
            st.warning(f"Sale logged perfectly, but inventory deduction failed: {e}")

        # ==========================================
        #  PHASE 1: REAL-TIME INVENTORY SYNC
        # ==========================================
        try:
            cart_items_for_sync = []
        
            # 1. Extract valid SKUs and quantities from the line items
            for _, row in line_items_df.iterrows():
                sku = str(row.get('Item_SKU', '')).strip()
                qty = row.get('Quantity', 0)
            
                # Skip custom items or blanks that shouldn't affect the Sourcing Vault
                if sku and sku.upper() != 'N/A':
                    try:
                        if int(qty) > 0:
                            cart_items_for_sync.append({'sku': sku, 'qty': int(qty)})
                    except ValueError:
                        pass
                    
            # 2. Fire the batch payload
            if cart_items_for_sync:
                sync_success = batch_deduct_inventory(cart_items_for_sync)
                if not sync_success:
                    logging.warning("Financial sale logged successfully, but inventory sync failed.")
                
        except Exception as e:
            logging.error(f"Inventory Sync Integration Error: {e}", exc_info=True)

        return True
        
    except Exception as e:
        st.error(f"Failed to log sale to database: {e}")
        return False

@st.cache_data(ttl=60) # Caches the data for 60 seconds to prevent API rate limit crashes
def load_sales_data():
    """
    Fetches the entire Sales_Engine database and returns it as a Pandas DataFrame.
    """
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds_dict.pop("spreadsheet_id", None)
        
        client_gspread = gspread.service_account_from_dict(creds_dict)
        sheet_id = st.secrets.get("spreadsheet_id") or st.secrets.get("gcp_service_account", {}).get("spreadsheet_id")
        
        if sheet_id:
            try:
                sh = client_gspread.open_by_key(sheet_id)
            except Exception:
                sh = client_gspread.open("Jewelry Business DB")
        else:
            sh = client_gspread.open("Jewelry Business DB")
            
        sheet = sh.worksheet("Sales_Engine")
        
        # Pull all data and convert to DataFrame
        records = sheet.get_all_records()

        df = pd.DataFrame(records)
        df.columns = df.columns.str.strip()
        
        return df
        
    except Exception as e:
        st.error(f"Failed to load sales data: {e}")
        return pd.DataFrame()