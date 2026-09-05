import streamlit as st
import logging
from sqlalchemy import text

def log_new_sale(formal_name, handle, line_items_df, total_pieces, total_cost, courier, amount_paid, payment_status):
    """
    Logs a new transaction securely to the PostgreSQL database.
    """
    try:
        # Convert the cart dataframe into a JSON string to store in the JSONB column
        line_items_json = line_items_df.to_json(orient='records')
        
        conn = st.connection("postgresql", type="sql")
        
        with conn.session as session:
            session.execute(
                text("""
                    INSERT INTO sales (
                        formal_name, handle, total_pieces, total_cost, 
                        courier_charge, amount_paid, payment_status, line_items
                    ) VALUES (
                        :formal_name, :handle, :total_pieces, :total_cost, 
                        :courier, :amount_paid, :payment_status, :line_items::jsonb
                    )
                """),
                {
                    "formal_name": formal_name,
                    "handle": handle,
                    "total_pieces": int(total_pieces),
                    "total_cost": float(total_cost),
                    "courier": float(courier),
                    "amount_paid": float(amount_paid),
                    "payment_status": payment_status,
                    "line_items": line_items_json
                }
            )
            session.commit()
            
        return True
        
    except Exception as e:
        logging.error(f"Failed to log sale to DB: {e}", exc_info=True)
        st.error(f"🚨 Failed to log transaction: {str(e)}")
        return False