import pandas as pd
from fpdf import FPDF
import io

def engine_automated_invoicing(latest_sale):
    """
    Generates a beautifully formatted PDF receipt with brand colors, 
    dynamic Invoice IDs, and clickable hyperlinks.
    """
    pdf = FPDF(orientation="P", unit="mm", format="A5") 
    pdf.add_page()
    
    # 1. Auto-Generate Invoice ID
    sale_date = latest_sale['Date of Sale']
    date_str = sale_date.strftime('%y%m%d') if pd.notnull(sale_date) else pd.Timestamp.today().strftime('%y%m%d')
    client_name = str(latest_sale['Instagram/Facebook Handle']).strip().upper()
    client_prefix = client_name[:3] if len(client_name) >= 3 else client_name.ljust(3, 'X')
    inv_id = f"INV-{date_str}-{client_prefix}"
    
    # 2. Brand Header (Deep Maroon)
    pdf.set_text_color(128, 0, 0) # RGB for Deep Maroon
    pdf.set_font("helvetica", "B", 18)
    pdf.cell(0, 10, "CHICK N CHAM", align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_text_color(100, 100, 100) # Soft grey for tagline
    pdf.set_font("helvetica", "I", 10)
    pdf.cell(0, 5, "Handpicked Artificial Jewelry", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)
    
    # 3. Invoice Details
    pdf.set_text_color(0, 0, 0) # Reset to black
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(40, 6, "Invoice ID:", border=0)
    pdf.set_font("helvetica", "", 9)
    pdf.cell(0, 6, inv_id, border=0, new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(40, 6, "Invoice Date:", border=0)
    pdf.set_font("helvetica", "", 9)
    formatted_date = sale_date.strftime('%Y-%m-%d') if pd.notnull(sale_date) else "N/A"
    pdf.cell(0, 6, formatted_date, border=0, new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(40, 6, "Billed To:", border=0)
    pdf.set_font("helvetica", "", 9)
    pdf.cell(0, 6, str(latest_sale['Instagram/Facebook Handle']), border=0, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    
    # 4. Modern Table Header (Light Grey Fill)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(70, 8, "Item Description", border=0, align="L", fill=True)
    pdf.cell(20, 8, "Qty", border=0, align="C", fill=True)
    pdf.cell(40, 8, "Amount", border=0, align="R", fill=True, new_x="LMARGIN", new_y="NEXT")
    
    # 5. Table Body with Faint Bottom Border
    pdf.set_font("helvetica", "", 9)
    qty = str(latest_sale.get('Total Pieces Sold', 1))
    item_desc = str(latest_sale['Items Sold Summary'])
    amount_str = f"INR {latest_sale['Total Amount Client Paid You']}"
    
    pdf.cell(70, 10, item_desc, border="B", align="L")
    pdf.cell(20, 10, qty, border="B", align="C")
    pdf.cell(40, 10, amount_str, border="B", align="R", new_x="LMARGIN", new_y="NEXT")
    
    # 6. Footer & Clickable Hyperlink
    pdf.ln(15) 
    pdf.set_text_color(50, 50, 50) 
    pdf.set_font("helvetica", "I", 9) # Changed from 'arial' to native 'helvetica' for cross-platform stability
    pdf.cell(0, 5, "Thank you for shopping with Chick n Cham!", align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_text_color(0, 102, 204) # Subtle link blue
    pdf.set_font("helvetica", "U", 9)
    pdf.cell(0, 5, "Follow us on Instagram @Chick_n_Cham_by_laddi", align="C", link="https://www.instagram.com/chik_n_cham_by_laddi/?hl=en")
    
    # Output to byte stream
    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    
    return pdf_buffer