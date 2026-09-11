import pandas as pd
import streamlit as st
from sqlalchemy import text
import logging

class BusinessRepository:
    """Abstracts database operations so the underlying store can change later."""
    
    @staticmethod
    def get_sales_data() -> pd.DataFrame:
        """Reads all past sales and transactions from Neon PostgreSQL."""
        try:
            conn = st.connection("postgresql", type="sql")
            
            # Use a 10-minute cache (ttl="10m") to prevent DB hammering. 
            # Write operations (POS/Corrections) will automatically clear this cache when new data is added.
            query = "SELECT * FROM sales ORDER BY id ASC;"
            df = conn.query(query, ttl="10m")
            
            return df
            
        except Exception as e:
            logging.error(f"Sales Database Read Error: {e}", exc_info=True)
            st.error("🚨 Failed to connect to the secure sales database.")
            return pd.DataFrame()

    @staticmethod
    def get_sourcing_data() -> pd.DataFrame:
        """Reads jewelry catalog and inventory data from Neon PostgreSQL."""
        try:
            conn = st.connection("postgresql", type="sql")
            
            # Map SQL columns EXACTLY to the legacy Google Sheets headers
            query = """
                SELECT 
                    sku AS "Item_SKU",
                    cost_price AS "Sourcing_Price",
                    tags AS "tags",
                    image_url AS "image_url",
                    standard_price AS "Standard_Price",
                    vip_price AS "VIP_Price",
                    clearance_price AS "Clearance_Price",
                    stock_quantity AS "Stock_Quantity"
                FROM sourcing_vault
                ORDER BY sku ASC;
            """
            
            df = conn.query(query, ttl="10m")
            return df
            
        except Exception as e:
            logging.error(f"Inventory Database Read Error: {e}", exc_info=True)
            st.error("🚨 Failed to connect to the inventory database.")
            return pd.DataFrame()

    @staticmethod
    def update_transaction(order_id: str, new_amount: float, new_status: str, new_client_name: str) -> bool:
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
                        "client_name": str(new_client_name).strip(),
                        "amount": float(new_amount),
                        "status": str(new_status).strip(),
                        "order_id": int(order_id)
                    }
                )
                session.commit()
            return True
            
        except Exception as e:
            logging.error(f"Database Update Error: {e}", exc_info=True)
            return False