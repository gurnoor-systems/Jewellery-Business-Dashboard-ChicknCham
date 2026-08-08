import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fpdf import FPDF
import io

# ==========================================
# 1. UI/UX & SYSTEM CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Chik n Cham by laddi 💎", 
    page_icon="💎", 
    layout="wide"
)

# ==========================================
# 2. DATA SECURITY (Authentication)
# ==========================================
@st.cache_resource
def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

# ==========================================
# 3. SYSTEM LOGIC (Data Ingestion)
# ==========================================
@st.cache_data(ttl=600) 
def load_data():
    client = init_connection()
    sheet = client.open("Jewelry Business DB")
    
    df_sales = pd.DataFrame(sheet.worksheet("Sales_Engine").get_all_records())
    df_sourcing = pd.DataFrame(sheet.worksheet("Sourcing_Engine").get_all_records())
    
    # DEFENSE 1: If the database is completely empty, stop processing and return the empty frames
    if df_sales.empty or df_sourcing.empty:
        return df_sales, df_sourcing
        
    # DEFENSE 2: Strip invisible trailing spaces from the Google Sheet column headers
    df_sales.columns = df_sales.columns.str.strip()
    df_sourcing.columns = df_sourcing.columns.str.strip()
    
    # DEFENSE 3: Only format the dates if the column actually exists to prevent crashes
    if 'Date of Sale' in df_sales.columns:
        # We use pd.to_datetime with infer_datetime_format to catch varying Google Sheets date formats
        df_sales['Date of Sale'] = pd.to_datetime(df_sales['Date of Sale'], errors='coerce')
    else:
        # If it fails, print exactly what columns it DID find so we can debug instantly
        raise KeyError(f"Could not find 'Date of Sale'. Columns found: {list(df_sales.columns)}")
        
    if 'Date of Purchase' in df_sourcing.columns:
        df_sourcing['Date of Purchase'] = pd.to_datetime(df_sourcing['Date of Purchase'], errors='coerce')
        
    return df_sales, df_sourcing

# ==========================================
# 4. SYSTEM INTEGRATION: CORE ENGINES
# ==========================================

def engine_cost_profitability(df_sales, df_sourcing):
    """
    Step 2: The Cost & Profitability Engine.
    Calculates True Profit, top performers, and Dead Stock alerts.
    """
    # 1. Core Financial KPIs
    total_sales = df_sales[df_sales['Payment Status'] == 'Paid (UPI/Bank)']['Total Amount Client Paid You'].sum()
    true_profit = df_sales[df_sales['Payment Status'] == 'Paid (UPI/Bank)']['True Profit'].sum()
    
    # 2. Identify Top Performer
    top_performer = "N/A"
    if not df_sales.empty:
        top_performer = df_sales.groupby('Items Sold Summary')['Total Amount Client Paid You'].sum().idxmax()
        
    # 3. Dead Stock Alert (Capital tied up in trips > 45 days ago)
    cutoff_date = pd.Timestamp.today() - pd.Timedelta(days=45)
    dead_stock_trips = df_sourcing[df_sourcing['Date of Purchase'] < cutoff_date]
    dead_stock_capital = dead_stock_trips['Total Amount'].sum()
    
    return total_sales, true_profit, top_performer, dead_stock_capital

def engine_automated_invoicing(latest_sale):
    """
    Step 3: Automated Customer Invoicing.
    Generates a beautifully formatted PDF receipt with brand colors, 
    dynamic Invoice IDs, and clickable hyperlinks.
    """
    pdf = FPDF(orientation="P", unit="mm", format="A5") 
    pdf.add_page()
    
    # 1. Auto-Generate Invoice ID (e.g., INV-260808-GUR)
    sale_date = latest_sale['Date of Sale']
    # Format date to YYMMDD
    date_str = sale_date.strftime('%y%m%d') if pd.notnull(sale_date) else pd.Timestamp.today().strftime('%y%m%d')
    # Get first 3 letters of client handle, padded with X if too short
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
    pdf.set_fill_color(240, 240, 240) # RGB for soft light grey
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(70, 8, "Item Description", border=0, align="L", fill=True)
    pdf.cell(20, 8, "Qty", border=0, align="C", fill=True)
    pdf.cell(40, 8, "Amount", border=0, align="R", fill=True, new_x="LMARGIN", new_y="NEXT")
    
    # 5. Table Body with Faint Bottom Border
    pdf.set_font("helvetica", "", 9)
    
    # Fetch quantity safely, default to 1 if it somehow fails
    qty = str(latest_sale.get('Total Pieces Sold', 1))
    item_desc = str(latest_sale['Items Sold Summary'])
    amount_str = f"INR {latest_sale['Total Amount Client Paid You']}"
    
    # "B" creates a bottom border only
    pdf.cell(70, 10, item_desc, border="B", align="L")
    pdf.cell(20, 10, qty, border="B", align="C")
    pdf.cell(40, 10, amount_str, border="B", align="R", new_x="LMARGIN", new_y="NEXT")
    
    # 6. Footer & Clickable Hyperlink
    pdf.ln(15) 
    pdf.set_text_color(50, 50, 50) 
    pdf.set_font("arial", "H", 9)
    pdf.cell(0, 5, "Thank you for shopping with Chick n Cham!", align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_text_color(0, 102, 204) # Subtle link blue
    pdf.set_font("helvetica", "U", 9)
    pdf.cell(0, 5, "Follow us on Instagram @Chick_n_Cham_by_laddi", align="C", link="https://www.instagram.com/chik_n_cham_by_laddi/?hl=en#")
    
    
    # Output to byte stream
    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    
    return pdf_buffer

def engine_vip_loyalty(df_sales):
    """
    Step 4: The VIP Loyalty Dashboard.
    Parses client IDs, calculates lifetime value, and flags repeat buyers.
    """
    # 1. Screen for valid, completed transactions only
    df_cleared = df_sales[df_sales['Payment Status'] == 'Paid (UPI/Bank)'].copy()
    
    # 2. Group by Client ID to calculate fundamental LTV metrics
    vip_df = df_cleared.groupby('Instagram/Facebook Handle').agg(
        Total_Orders=('Instagram/Facebook Handle', 'count'),
        Lifetime_Spend=('Total Amount Client Paid You', 'sum'),
        Total_Profit=('True Profit', 'sum')
    ).reset_index()
    
    # 3. Sort by highest Lifetime Spend to generate the 80/20 list
    vip_df = vip_df.sort_values(by='Lifetime_Spend', ascending=False)
    
    # 4. Flag repeat buyers programmatically
    vip_df['Client Status'] = vip_df['Total_Orders'].apply(
        lambda x: '⭐ VIP Repeat' if x > 1 else 'New'
    )
    
    return vip_df
# ==========================================
# 5. DASHBOARD PRESENTATION
# ==========================================
def main():
    st.title("💎 Chick n Cham by laddi")
    st.markdown("### Operations & Intelligence Command Center")
    
    try:
        with st.spinner("Syncing secure database..."):
            df_sales, df_sourcing = load_data()
            
        tab1, tab2, tab3 = st.tabs([
            "📊 Profitability Engine", 
            "👑 VIP Loyalty Dashboard", 
            "🧾 Invoicing & Automation"
        ])
        
        with tab1:
            st.subheader("Financial Command Center")
            
            if not df_sales.empty and not df_sourcing.empty:
                sales, profit, top_item, dead_capital = engine_cost_profitability(df_sales, df_sourcing)
                
                # KPI Cards
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Realized Revenue", f"₹{sales:,.0f}")
                col2.metric("True Net Profit", f"₹{profit:,.0f}")
                col3.metric("Top Performer", top_item)
                col4.metric("⚠️ 45-Day Dead Stock", f"₹{dead_capital:,.0f}", delta="Capital Trapped", delta_color="inverse")
                
                st.divider()
                
                # WhatsApp Summary Generator
                st.markdown("#### 📱 Weekly WhatsApp Summary")
                st.info("Copy this summary to send directly to the business owner.")
                summary_text = (
                    f"📊 *Weekly Operations Update*\n"
                    f"Total Sales: ₹{sales:,.0f}\n"
                    f"True Profit: ₹{profit:,.0f}\n"
                    f"🔥 Top Performer: {top_item}\n"
                    f"⚠️ Note: You have ₹{dead_capital:,.0f} tied up in stock older than 45 days. Consider discounting older pieces on the next live!"
                )
                st.code(summary_text, language="markdown")
                
            else:
                st.warning("Insufficient data to calculate profitability.")
            
        with tab2:
            st.subheader("Client Lifetime Value (CLV) Screener")
            st.markdown("Use this intelligence to prioritize DMs and offer exclusive sneak peeks before live sessions.")
            
            # Verification: Ensure data exists before running calculations
            if not df_sales.empty and 'Instagram/Facebook Handle' in df_sales.columns:
                vip_data = engine_vip_loyalty(df_sales)
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown("#### 🏆 Top 10 High-Value Clients")
                    st.dataframe(
                        vip_data.head(10),
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Instagram/Facebook Handle": "Client Handle",
                            "Total_Orders": "Orders",
                            "Lifetime_Spend": st.column_config.NumberColumn("Lifetime Spend (₹)", format="₹%d"),
                            "Total_Profit": st.column_config.NumberColumn("Total Profit (₹)", format="₹%d"),
                            "Client Status": "Status"
                        }
                    )
                
                with col2:
                    st.markdown("#### 💡 Actionable Insights")
                    repeat_count = len(vip_data[vip_data['Total_Orders'] > 1])
                    total_clients = len(vip_data)
                    repeat_rate = (repeat_count / total_clients) * 100 if total_clients > 0 else 0
                    
                    st.metric(label="Total Repeat Buyers", value=repeat_count)
                    st.metric(label="Repeat Customer Rate", value=f"{repeat_rate:.1f}%")
                    
                    st.info("Message the top 3 clients on this list whenever a new Sadar shipment arrives. Converting these existing buyers costs ₹0 in marketing.")
            else:
                st.warning("No sales data available yet to generate VIP list.")
            
        with tab3:
            st.subheader("🧾 Invoice Generator")
            st.markdown("Generate professional PDF receipts for your most recent cleared orders.")
            
            # Filter for valid sales
            df_valid_sales = df_sales[df_sales['Payment Status'].isin(['Paid (UPI/Bank)', 'COD (Pending)'])].copy()
            
            if not df_valid_sales.empty:
                # Get the 5 most recent orders
                recent_orders = df_valid_sales.sort_values(by='Date of Sale', ascending=False).head(5)
                
                for index, row in recent_orders.iterrows():
                    client = row['Instagram/Facebook Handle']
                    item = row['Items Sold Summary']
                    amount = row['Total Amount Client Paid You']
                    
                    with st.container(border=True):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.markdown(f"**Client:** {client}")
                            st.caption(f"Item: {item} | Total: ₹{amount}")
                            
                        with col2:
                            # Generate the PDF in memory
                            pdf_bytes = engine_automated_invoicing(row)
                            
                            # Create a download button
                            st.download_button(
                                label="⬇️ Download PDF",
                                data=pdf_bytes,
                                file_name=f"ChickNCham_Receipt_{client}.pdf",
                                mime="application/pdf",
                                key=f"btn_{index}"
                            )
            else:
                st.info("No recent valid orders found to invoice.")
            
    except Exception as e:
        st.error(f"Database Connection Error: {e}")

if __name__ == "__main__":
    main()