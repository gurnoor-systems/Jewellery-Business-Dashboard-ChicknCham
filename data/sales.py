import streamlit as st
import pandas as pd
import logging
from datetime import datetime
import time

def log_new_sale(formal_name, handle, line_items_df, total_pieces, total_cost, courier, amount_paid, payment_status):
    """
    Logs a new transaction securely to the PostgreSQL database.
    """
    try:
        now = datetime.now()
        
        new_sale_df = pd.DataFrame([{
            "Order_ID": int(time.time()),  # Generates a unique timestamp-based ID
            "Timestamp": now.strftime("%d/%m/%Y %H:%M:%S"),
            "Date of Sale": now.strftime("%B %d, %Y"),
            "Client Formal Name": formal_name,
            "Instagram/Facebook Handle": handle,
            "Line_Items_JSON": line_items_df.to_json(orient='records'),
            "Total Pieces Sold": int(total_pieces),
            "Total Cost of These Items": float(total_cost),
            "Courier Charge You Paid": float(courier),
            "Total Amount Client Paid You": float(amount_paid),
            "Payment Status": payment_status
        }])
        
        conn = st.connection("postgresql", type="sql")
        
        # Append safely to the sales_ledger table
        new_sale_df.to_sql('sales_ledger', conn.engine, if_exists='append', index=False)
        
        return True
        
    except Exception as e:
        logging.error(f"Failed to log sale to DB: {e}", exc_info=True)
        st.error(f"🚨 Failed to log transaction: {str(e)}")
        return False