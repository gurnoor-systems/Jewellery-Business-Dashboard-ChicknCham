import streamlit as st
import pandas as pd
from PIL import Image
import io
import logging
from sqlalchemy import text

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
    Appends a new cataloged item directly to the PostgreSQL sourcing_vault table.
    """
    try:
        conn = st.connection("postgresql", type="sql")
        with conn.session as session:
            query = text("""
                INSERT INTO sourcing_vault 
                (sku, cost_price, tags, image_url, standard_price, vip_price, clearance_price, stock_quantity) 
                VALUES (:sku, :price, :tags, :image_url, :std_price, :vip_price, :clr_price, :stock_qty)
            """)
            session.execute(query, {
                "sku": sku, 
                "price": price, 
                "tags": tags, 
                "image_url": image_url, 
                "std_price": std_price, 
                "vip_price": vip_price, 
                "clr_price": clr_price, 
                "stock_qty": stock_qty
            })
            session.commit()
        return True
    except Exception as e:
        # Fallback: If DB schema is missing new columns, Pandas will auto-append them safely
        try:
            logging.warning(f"SQL Insert missed schema, attempting Pandas fallback. Error: {e}")
            df = pd.DataFrame([{
                "sku": sku, 
                "cost_price": price, 
                "tags": tags, 
                "image_url": image_url, 
                "standard_price": std_price, 
                "vip_price": vip_price, 
                "clearance_price": clr_price, 
                "stock_quantity": stock_qty
            }])
            conn = st.connection("postgresql", type="sql")
            df.to_sql('sourcing_vault', conn.engine, if_exists='append', index=False)
            return True
        except Exception as inner_e:
            logging.error(f"Failed to insert into PostgreSQL: {inner_e}", exc_info=True)
            return False

def delete_from_sourcing_vault(sku):
    """
    Finds the specific SKU in the database and deletes the entire row.
    """
    try:
        conn = st.connection("postgresql", type="sql")
        with conn.session as session:
            session.execute(
                text("DELETE FROM sourcing_vault WHERE sku = :sku"),
                {"sku": sku}
            )
            session.commit()
        return True
    except Exception as e:
        logging.error(f"PostgreSQL Deletion Failure: {e}", exc_info=True)
        return False

def batch_deduct_inventory(cart_items):
    """
    Deducts stock for a batch of SKUs in a single PostgreSQL transaction.
    Expects cart_items as a list of dicts: [{'sku': 'JK-123...', 'qty': 2}, ...]
    """
    if not cart_items:
        return True

    try:
        conn = st.connection("postgresql", type="sql")
        with conn.session as session:
            for item in cart_items:
                # GREATEST(0, ...) prevents stock from dropping below zero
                session.execute(
                    text("""
                        UPDATE sourcing_vault 
                        SET stock_quantity = GREATEST(0, stock_quantity - :qty) 
                        WHERE sku = :sku
                    """),
                    {"qty": int(item['qty']), "sku": str(item['sku'])}
                )
            session.commit()
        return True
    except Exception as e:
        logging.error(f"Batch Inventory Deduct Failure: {e}", exc_info=True)
        return False

def restock_inventory(sku, additional_qty):
    """
    Increases the stock quantity for a specific SKU.
    """
    if additional_qty <= 0:
        return True
        
    try:
        conn = st.connection("postgresql", type="sql")
        with conn.session as session:
            session.execute(
                text("""
                    UPDATE sourcing_vault 
                    SET stock_quantity = stock_quantity + :qty 
                    WHERE sku = :sku
                """),
                {"qty": int(additional_qty), "sku": sku}
            )
            session.commit()
        return True
    except Exception as e:
        logging.error(f"Restock Failure: {e}", exc_info=True)
        return False