import pandas as pd
import streamlit as st
from sqlalchemy import text

class BusinessRepository:
    """Abstracts database operations so the underlying store can change later."""
    
    @staticmethod
    def get_sales_data() -> pd.DataFrame:
        """Reads sales data from Neon PostgreSQL."""
        try:
            conn = st.connection("postgresql", type="sql")
            
            # Map SQL columns to exact Google Sheets headers so frontend views do not break
            query = """
                SELECT 
                    id AS "Order_ID",
                    created_at AS "Date",
                    formal_name AS "Client Formal Name",
                    handle AS "Instagram/Facebook Handle",
                    total_pieces AS "Total Pieces",
                    total_cost AS "Total Sourcing Cost",
                    courier_charge AS "Courier Charge",
                    amount_paid AS "Total Amount Client Paid You",
                    payment_status AS "Payment Status",
                    line_items AS "Line Items"
                FROM sales 
                ORDER BY id DESC;
            """
            
            # ttl=0 ensures the POS system fetches real-time data on every refresh
            df = conn.query(query, ttl=0)
            return df
            
        except Exception as e:
            st.error(f"Database Read Error: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_sourcing_data() -> pd.DataFrame:
        """Returns an empty DataFrame until the catalog table is migrated."""
        return pd.DataFrame()

    @staticmethod
    def update_transaction(order_id: str, new_amount: float, new_status: str, new_client_name: str):
        """Safely updates a sales transaction row in PostgreSQL by Order_ID."""
        try:
            conn = st.connection("postgresql", type="sql")
            
            # Use SQLAlchemy session for safe, parameterized writes
            with conn.session as session:
                session.execute(
                    text("""
                        UPDATE sales 
                        SET formal_name = :client_name, 
                            amount_paid = :amount, 
                            payment_status = :status 
                        WHERE id = :order_id
                    """),
                    {
                        "client_name": new_client_name,
                        "amount": float(new_amount),
                        "status": new_status,
                        "order_id": int(order_id)
                    }
                )
                session.commit()
            return True
            
        except Exception as e:
            st.error(f"Database Update Error: {e}")
            return str(e)