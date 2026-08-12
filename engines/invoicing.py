import json
import pandas as pd
from fpdf import FPDF
import streamlit as st

def generate_invoice_pdf(transaction_row):
    """
    Parses the JSON line items from a database row and builds a formal PDF receipt.
    """
    try:
        # Extract variables
        client_name = str(transaction_row.get("Client Formal Name", "Valued Client"))
        date_of_sale = str(transaction_row.get("Date of Sale", "N/A"))
        timestamp = str(transaction_row.get("Timestamp", "N/A"))
        total_paid = float(transaction_row.get("Total Amount Client Paid You", 0.0))
        json_string = str(transaction_row.get("Line_Items_JSON", "[]"))
        
        # Parse JSON
        try:
            line_items = json.loads(json_string)
        except Exception:
            line_items = [{"Category": "Item", "Quantity": 1, "Unit Price (₹)": total_paid}]

        # Initialize PDF
        pdf = FPDF()
        pdf.add_page()
        
        # --- HEADER ---
        pdf.set_text_color(128, 0, 0) # Maroon
        pdf.set_font("Helvetica", "B", 24)
        pdf.cell(0, 10, "chik n cham", ln=True, align="C")
        
        pdf.set_text_color(128, 128, 128) # Gray
        pdf.set_font("Helvetica", "I", 12)
        pdf.cell(0, 8, "Handpicked Artificial Jewelry", ln=True, align="C")
        
        pdf.set_text_color(0, 0, 0)
        pdf.ln(10)
        
        # --- CLIENT & ORDER INFO ---
        pdf.set_font("Helvetica", "B", 11)
        # Generate a cleaner invoice ID
        clean_id = timestamp.replace('/', '').replace(':', '').replace(' ', '')[-6:]
        
        pdf.cell(100, 8, f"Billed To: {client_name}", ln=False)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 9, f"Date: {date_of_sale}", ln=True, align="R")
        
        pdf.cell(100, 8, "", ln=False)
        pdf.cell(0, 9, f"Invoice ID: INV-{clean_id}", ln=True, align="R")
        pdf.ln(10)
        
        # --- TABLE HEADER ---
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(245, 235, 235)  # Pastel maroon/pink tint
        pdf.set_draw_color(200, 200, 200)  # Lighter, cleaner borders
        
        pdf.cell(85, 10, "Item Description", border=1, align="L", fill=True)
        pdf.cell(30, 10, "Qty", border=1, align="C", fill=True)
        pdf.cell(40, 10, "Unit Price", border=1, align="C", fill=True)
        pdf.cell(35, 10, "Amount", border=1, align="C", fill=True)
        pdf.ln()
        
        # --- TABLE ROWS ---
        pdf.set_font("Helvetica", "", 10)
        for item in line_items:
            cat = str(item.get("Category", "Item"))
            custom = str(item.get("Custom Details", "")).strip()
            qty = int(item.get("Quantity", 1))
            unit_price = float(item.get("Unit Price (₹)", 0.0))
            line_total = qty * unit_price

            if cat.lower() == "other" and custom:
                display_name = custom
            elif custom:
                display_name = f"{cat} ({custom})"
            else:
                display_name = cat
                
            # Truncate text if it's too long so it doesn't break the PDF table border
            if len(display_name) > 35:
                display_name = display_name[:32] + ".."
            
            # Slightly increased row height (10) for better readability
            pdf.cell(85, 10, f"  {cat}", border=1) # Added space for padding
            pdf.cell(30, 10, str(qty), border=1, align="C")
            pdf.cell(40, 10, f"INR {unit_price:,.2f}  ", border=1, align="R")
            pdf.cell(35, 10, f"INR {line_total:,.2f}  ", border=1, align="R")
            pdf.ln()
            
        # --- GRAND TOTAL ---
        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(155, 10, "Grand Total Paid:", align="R")
        pdf.cell(35, 10, f"INR {total_paid:,.2f}  ", align="R")
        
        # --- FOOTER & CTA ---
        pdf.ln(30)
        
        # Top line of the CTA
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(128, 0, 0) # Brand Maroon
        pdf.cell(0, 6, "Love your new pieces? Tag us in your stories", ln=True, align="C")
        
        # Bottom line with the hyperlink
        pdf.set_text_color(0, 0, 255) # Link Blue
        pdf.set_font("Helvetica", "UB", 10) # Underlined and Bold
        pdf.cell(0, 6, "@chik_n_cham_by_laddi for 10% off your next order!", align="C", link="https://instagram.com/Chik_n_Cham_by_laddi")
        
        return bytes(pdf.output())
        
    except Exception as e:
        return f"Error generating PDF: {str(e)}"