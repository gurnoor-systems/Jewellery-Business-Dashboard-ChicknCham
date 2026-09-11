import streamlit as st
import pandas as pd
import logging
from sqlalchemy import text

def log_new_sale(formal_name, handle, line_items_df, total_pieces, total_cost, courier, amount_paid, payment_status):
    """Securely logs a transaction, enforcing strict schema types and clean JSONB casting."""
    try:
        # Convert DataFrame to a clean JSON string for PostgreSQL
        line_items_json = line_items_df.to_json(orient='records')
        
        conn = st.connection("postgresql", type="sql")
        with conn.session as session:
            session.execute(
                text("""
                    INSERT INTO sales (formal_name, handle, total_pieces, total_cost, courier_charge, amount_paid, payment_status, line_items) 
                    VALUES (:formal_name, :handle, :total_pieces, :total_cost, :courier, :amount_paid, :payment_status, :line_items::jsonb)
                """),
                {
                    "formal_name": str(formal_name).strip().title(), 
                    "handle": str(handle).strip().lower(), # Force lowercase to prevent CRM fragmentation
                    "total_pieces": int(total_pieces), 
                    "total_cost": float(total_cost), 
                    "courier": float(courier), 
                    "amount_paid": float(amount_paid), 
                    "payment_status": str(payment_status).strip(), 
                    "line_items": line_items_json # Explicitly cast in query using ::jsonb
                }
            )
            session.commit()
        return True
    
    except Exception as e:
        logging.error(f"Failed to log sale to DB: {e}", exc_info=True)
        st.error(f"🚨 Failed to log transaction. Please check system logs.")
        return False