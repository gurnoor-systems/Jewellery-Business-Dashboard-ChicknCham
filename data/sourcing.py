import io
import logging
import pandas as pd
from PIL import Image
import streamlit as st
from sqlalchemy import text


def compress_image(image_bytes: bytes, max_size=(800, 800), quality: int = 80) -> bytes:
    """Compresses an image to standard dimensions and JPEG format."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.thumbnail(max_size)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality)
        return buffer.getvalue()
    except Exception as e:
        logging.error(f"Image Compression Error: {e}", exc_info=True)
        return image_bytes


def save_to_sourcing_vault(
    sku: str,
    price: float,
    tags: str,
    image_url: str,
    std_price: float,
    vip_price: float,
    clr_price: float,
    stock_qty: int
) -> bool:
    """Inserts a new cataloged item into PostgreSQL with strict type enforcement."""
    try:
        conn = st.connection("postgresql", type="sql")
        with conn.session as session:
            query = text("""
                INSERT INTO sourcing_vault 
                (sku, cost_price, tags, image_url, standard_price, vip_price, clearance_price, stock_quantity) 
                VALUES (:sku, :price, :tags, :image_url, :std_price, :vip_price, :clr_price, :stock_qty)
            """)
            session.execute(query, {
                "sku": str(sku).strip(),
                "price": float(price),
                "tags": str(tags).strip(),
                "image_url": str(image_url).strip(),
                "std_price": float(std_price),
                "vip_price": float(vip_price),
                "clr_price": float(clr_price),
                "stock_qty": int(stock_qty)
            })
            session.commit()
        return True
    except Exception as e:
        logging.error(f"PostgreSQL Sourcing Vault Insertion Error: {e}", exc_info=True)
        return False


def delete_from_sourcing_vault(sku: str) -> bool:
    """Permanently removes an item from PostgreSQL by SKU."""
    try:
        conn = st.connection("postgresql", type="sql")
        with conn.session as session:
            session.execute(
                text("DELETE FROM sourcing_vault WHERE sku = :sku"),
                {"sku": str(sku).strip()}
            )
            session.commit()
        return True
    except Exception as e:
        logging.error(f"PostgreSQL Deletion Failure for SKU {sku}: {e}", exc_info=True)
        return False


def batch_deduct_inventory(cart_items: list) -> bool:
    """
    Deducts stock for a batch of SKUs in a single atomic transaction.
    cart_items format: [{'sku': 'JK-...', 'qty': 2}, ...]
    """
    if not cart_items:
        return True

    try:
        conn = st.connection("postgresql", type="sql")
        with conn.session as session:
            for item in cart_items:
                session.execute(
                    text("""
                        UPDATE sourcing_vault 
                        SET stock_quantity = GREATEST(0, stock_quantity - :qty) 
                        WHERE sku = :sku
                    """),
                    {
                        "qty": int(item.get("qty", 1)),
                        "sku": str(item.get("sku", "")).strip()
                    }
                )
            session.commit()
        return True
    except Exception as e:
        logging.error(f"Batch Inventory Deduct Failure: {e}", exc_info=True)
        return False


def restock_inventory(sku: str, additional_qty: int) -> bool:
    """Increments stock count for an existing item in PostgreSQL."""
    if int(additional_qty) <= 0:
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
                {
                    "qty": int(additional_qty),
                    "sku": str(sku).strip()
                }
            )
            session.commit()
        return True
    except Exception as e:
        logging.error(f"Restock Failure for SKU {sku}: {e}", exc_info=True)
        return False