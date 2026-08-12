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
        
        # Header: Maroon Title
        pdf.set_text_color(128, 0, 0) 
        pdf.set_font("Helvetica", "B", 24)
        pdf.cell(0, 10, "CHICK N CHAM", ln=True, align="C")
        
        # Subtitle: Gray Italics
        pdf.set_text_color(128, 128, 128)
        pdf.set_font("Helvetica", "I", 12)
        pdf.cell(0, 8, "Handpicked Artificial Jewelry", ln=True, align="C")
        
        # Reset color to black
        pdf.set_text_color(0, 0, 0)
        pdf.ln(10)
        
        # Client & Order Info
        pdf.set_font("Helvetica", "B", 11)
        # Generate a cleaner invoice ID
        clean_id = timestamp.replace('/', '').replace(':', '').replace(' ', '')[-6:]
        
        pdf.cell(100, 8, f"Billed To: {client_name}", ln=False)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 8, f"Date: {date_of_sale}", ln=True, align="R")
        
        pdf.cell(100, 8, "", ln=False) # Spacer
        pdf.cell(0, 8, f"Invoice ID: INV-{clean_id}", ln=True, align="R")
        pdf.ln(10)
        
        # Table Header
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(85, 10, "Item Description", border=1, fill=True)
        pdf.cell(30, 10, "Qty", border=1, align="C", fill=True)
        pdf.cell(40, 10, "Unit Price", border=1, align="R", fill=True)
        pdf.cell(35, 10, "Amount", border=1, align="R", fill=True)
        pdf.ln()
        
        # Table Rows
        pdf.set_font("Helvetica", "", 10)
        for item in line_items:
            cat = str(item.get("Category", "Item"))
            qty = int(item.get("Quantity", 1))
            unit_price = float(item.get("Unit Price (₹)", 0.0))
            line_total = qty * unit_price
            
            pdf.cell(85, 10, cat, border=1)
            pdf.cell(30, 10, str(qty), border=1, align="C")
            pdf.cell(40, 10, f"INR {unit_price:,.2f}", border=1, align="R")
            pdf.cell(35, 10, f"INR {line_total:,.2f}", border=1, align="R")
            pdf.ln()
            
        # Grand Total
        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(155, 10, "Grand Total Paid:", align="R")
        pdf.cell(35, 10, f"INR {total_paid:,.2f}", align="R")
        
        # Footer
        pdf.ln(30)
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 6, "Thank you for shopping with Chick n Cham!", ln=True, align="C")
        
        # Blue Hyperlink
        pdf.set_text_color(0, 0, 255)
        pdf.set_font("Helvetica", "U", 10)
        pdf.cell(0, 6, "Follow us on Instagram @Chick_n_Cham_by_laddi", align="C", link="https://instagram.com/Chick_n_Cham_by_laddi")
        
        return bytes(pdf.output())
        
    except Exception as e:
        return f"Error generating PDF: {str(e)}"