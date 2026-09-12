import streamlit as st
import pandas as pd
import logging
from sqlalchemy import text

def log_sale_and_deduct_atomic(formal_name, handle, line_items_df, total_pieces, total_cost, courier, amount_paid, payment_status):
    """
    Executes a strict atomic transaction. If the financial log OR the inventory deduction fails, 
    the entire operation rolls back to guarantee perfect ledger parity.
    """
    try:
        line_items_json = line_items_df.to_json(orient='records')
        conn = st.connection("postgresql", type="sql")
        
        # A single session block guarantees True Atomicity
        with conn.session as session:
            # 1. Financial Ledger Execution
            session.execute(
                text("""
                    INSERT INTO sales (formal_name, handle, total_pieces, total_cost, courier_charge, amount_paid, payment_status, line_items) 
                    VALUES (:formal_name, :handle, :total_pieces, :total_cost, :courier, :amount_paid, :payment_status, :line_items::jsonb)
                """),
                {
                    "formal_name": str(formal_name).strip().title(), 
                    "handle": str(handle).strip().lower(), 
                    "total_pieces": int(total_pieces), 
                    "total_cost": float(total_cost), 
                    "courier": float(courier), 
                    "amount_paid": float(amount_paid), 
                    "payment_status": str(payment_status).strip(), 
                    "line_items": line_items_json
                }
            )
            
            # 2. Inventory Settlement Execution
            # We iterate through the dataframe and execute deductions in the same transaction
            for _, item in line_items_df.iterrows():
                session.execute(
                    text("""
                        UPDATE sourcing_vault 
                        SET stock_quantity = GREATEST(0, stock_quantity - :qty) 
                        WHERE sku = :sku
                    """),
                    {
                        "qty": int(item["Quantity"]),
                        "sku": str(item["Item_SKU"]).strip()
                    }
                )
            
            # 3. Commit only if both phases succeed
            session.commit()
            
        return True
    
    except Exception as e:
        logging.error(f"Atomic Transaction Failed: {e}", exc_info=True)
        return False