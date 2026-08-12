import time
import uuid
import streamlit as st
import pandas as pd

# Data Imports

from data.ingestion import load_data, load_sourcing_vault
from data.storage import upload_to_cloudinary
from data.sourcing import compress_image, save_to_sourcing_vault
from data.sales import log_new_sale, load_sales_data

# Engine Imports

from engines.financials import engine_cost_profitability, generate_financial_charts, engine_cac_mom_growth
from engines.crm import engine_vip_loyalty
from engines.invoicing import generate_invoice_pdf
from engines.marketing import generate_instagram_captions
from engines.live_match import analyze_live_item, find_vault_match

# SKU Unique Identifier Generator


# ==========================================
# 1. UI/UX & SYSTEM CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Chick n Cham by laddi 💎", 
    page_icon="💎", 
    layout="wide"
)

# DEFENSE: Hide default Streamlit loading indicators and branding
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .block-container {
                padding-top: 2rem;
                padding-bottom: 0rem;
            }
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# ==========================================
# 2. SECURITY WALL
# ==========================================

def check_password():
    """Returns True if the user entered the correct password."""
    
    # 1. Fast-Pass: If already authenticated, skip the checks and grant access immediately.
    # This completely protects the app from logging you out during PDF downloads.
    if st.session_state.get("password_correct", False):
        return True
        
    # 2. Verification Logic
    def verify_password():
        if st.session_state.get("admin_password_input", "") == st.secrets["admin"]["password"]:
            st.session_state["password_correct"] = True
        else:
            st.session_state["password_correct"] = False
            
    # 3. Login UI
    st.markdown("### 🔐 Secure Login Required")
    st.text_input(
        "Enter Admin Password", 
        type="password", 
        on_change=verify_password, 
        key="admin_password_input" # Changed key name to prevent ghost memory from the old bug
    )
    
    # 4. Error Handling
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("🚫 Access Denied: Incorrect Password")
        
    return False

# ==========================================
# 3. DASHBOARD PRESENTATION
# ==========================================

def main():
    st.title("💎 Chick n Cham by laddi")
    st.markdown("### Current Operations")

    with st.sidebar:
        st.header("📈 Marketing Controls 📈")
        st.markdown("Enter your recent advertising spend to calculate acquisition costs.")

        weekly_spend = st.number_input(
            "Weekly Ad Spend (₹)", 
            min_value=0.0, 
            value=0.0,
            help="Enter any amount. Type directly or use arrows."
        )
        
    try:
        with st.spinner("Syncing secure database.."):
            df_sales, df_sourcing = load_data()
            
        tab1, tab2, tab4, tab5, tab6, tab7, tab3 = st.tabs([
            "📊 Profitability Dashboard", 
            "👑 Loyalty Dashboard", 
            "🎨 Content Generator",
            "🛒 Log Jewelry",
            "🔴 Jewelery info!",
            "🛒 Log a Sale",
            "🧾 Invoice"
        ])
        
        with tab1:
            st.subheader("Current Financial Health")
            if not df_sales.empty and not df_sourcing.empty:
                # 1. Run core calculations
                sales, profit, top_item, dead_capital = engine_cost_profitability(df_sales, df_sourcing)
                cac, new_clients, mom = engine_cac_mom_growth(df_sales, weekly_spend)

                # 2. Defensive Input Checks & Feedback

                if weekly_spend > 1_00_000:
                    st.error("🚨 The amount entered is exceptionally high (over ₹1 Lakh). Please verify the value in the sidebar.")

                # 3. Growth & Acquisition Section
                st.markdown("##### 🚀 Growth & Acquisition (Last 7 Days)")
                metric_col1, metric_col2, metric_col3 = st.columns(3)
                metric_col1.metric("MoM Revenue Growth", f"{mom:,.1f}%", delta=f"{mom:,.1f}%", delta_color="normal")
                metric_col2.metric("New Clients Acquired", new_clients)

                if weekly_spend > 0:
                    ui_cac_label = f"₹{cac:,.2f}"
                    wa_cac_label = f"₹{cac:,.2f}"
                    cac_delta = "Spend per Client"
                else:
                    ui_cac_label = "₹0 " 
                    wa_cac_label = "₹0 "
                    cac_delta = "Spend per Client"
                metric_col3.metric("Customer Acquisition Cost (CAC)", ui_cac_label, delta=cac_delta, delta_color="inverse")
                
                st.divider()

                # 4. Core Financial KPIs
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Realized Revenue", f"₹{sales:,.0f}")
                col2.metric("True Net Profit", f"₹{profit:,.0f}")
                col3.metric("Top Performer", top_item)
                col4.metric("⚠️ 45-Day Dead Stock", f"₹{dead_capital:,.0f}", delta="Capital Trapped", delta_color="inverse")
                
                st.divider()

                # 5. Interactive Charts
                fig_trend, fig_donut = generate_financial_charts(df_sales)
                if fig_trend and fig_donut:
                    chart_col1, chart_col2 = st.columns([3, 2])
                    with chart_col1:
                        st.plotly_chart(fig_trend, use_container_width=True)
                    with chart_col2:
                        st.plotly_chart(fig_donut, use_container_width=True)
                    st.divider()

                st.markdown("#### 📱 Weekly WhatsApp Summary")
                st.info("Copy this summary to send directly to the business owner.")
                summary_text = (
                    f"📊 *Weekly Operations Update*\n"
                    f"Total Sales: ₹{sales:,.0f}\n"
                    f"True Profit: ₹{profit:,.0f}\n"
                    f"🚀 MoM Growth: {mom:,.1f}%\n"
                    f"🎯 CAC: {wa_cac_label}/client (₹{weekly_spend:,.2f} total spend)\n"
                    f"🔥 Top Performer: {top_item}\n"
                    f"⚠️ Note: You have ₹{dead_capital:,.0f} tied up in stock older than 45 days. Consider discounting older pieces on the next live!"
                )
                st.code(summary_text, language="markdown")
            else:
                st.warning("Insufficient data to calculate profitability.")
            
        with tab2:
            st.subheader("Client Lifetime Value (CLV) Screener")
            st.markdown("Use this to prioritize DMs and offer exclusive sneak peeks before live sessions.")
            if not df_sales.empty and 'Instagram/Facebook Handle' in df_sales.columns:
                vip_data = engine_vip_loyalty(df_sales)
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown("#### 🏆 Top High-Value Clients")
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
                    st.info("Message the top clients whenever the new stock arrives. "
                    "Impact: Converting these existing buyers cost zero in marketing.")

            else:
                st.warning("No sales data available yet to generate VIP list.")
            
        with tab3:
            st.subheader("🧾 Invoice")
            st.caption("Select the transaction to fetch its Invoice.")
            
            # Load the sales database
            sales_df = load_sales_data()
            
            if not sales_df.empty and 'Client Formal Name' in sales_df.columns:
                # Filter out blank rows safely
                valid_sales = sales_df[sales_df['Client Formal Name'].astype(str).str.strip() != ""]
                
                if not valid_sales.empty:
                    # Sort by most recent first (using the index since newest rows are appended at the bottom)
                    recent_sales = valid_sales.iloc[::-1].head(10) 
                    
                    # Create a clean display string for the dropdown
                    recent_sales['Display'] = recent_sales['Date of Sale'].astype(str) + " - " + recent_sales['Client Formal Name'].astype(str) + " (₹" + recent_sales['Total Amount Client Paid You'].astype(str) + ")"
                    
                    selected_display = st.selectbox("Select Transaction", options=recent_sales['Display'].tolist())
                    
                    if selected_display:
                        # Extract the exact row based on the selection
                        selected_row = recent_sales[recent_sales['Display'] == selected_display].iloc[0]
                        
                        st.divider()
                        st.markdown(f"**Generating Invoice for:** {selected_row['Client Formal Name']}")
                        
                        # Generate the PDF
                        pdf_bytes = generate_invoice_pdf(selected_row)
                        
                        if isinstance(pdf_bytes, bytes):
                            # Create a dynamic filename
                            safe_name = str(selected_row['Client Formal Name']).replace(" ", "_")
                            file_name = f"Invoice_ChickNCham_{safe_name}.pdf"
                            
                            st.download_button(
                                label="📥 Download PDF Invoice",
                                data=pdf_bytes,
                                file_name=file_name,
                                mime="application/pdf",
                                type="primary",
                                use_container_width=True
                            )
                        else:
                            st.error(pdf_bytes) # Displays the error string if PDF generation fails
                else:
                    st.info("No valid transactions found with a formal client name.")
            else:
                st.warning("Database empty or missing structured columns. Log a sale first.")
        
        with tab4:
            st.subheader("✨ Caption Generator")
            st.markdown("Instantly generating engaging Instagram copy and hashtags for your latest drops.")
            
            with st.container(border=True):
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    prod_name = st.text_input("Product Name", placeholder="e.g., Heavy Kundan Bridal Set")
                    prod_price = st.number_input("Listing Price (₹)", min_value=0.0, step=100.0)
                    
                with col2:
                    prod_features = st.text_area("Key Features (Materials, Colors, Style)", placeholder="e.g., Mint green stones, gold-plated, perfect for weddings, lightweight")
                    
                submit_ai = st.button("🚀 Generate Captions", type="primary", use_container_width=True)
                
            if submit_ai:
                if prod_name and prod_features:
                    with st.spinner("Brainstorming .."):
                        generated_text = generate_instagram_captions(prod_name, prod_price, prod_features)
                        st.success("Captions Generated!")
                        st.help("Copy the text below")
                        st.markdown(generated_text)
                else:
                    st.warning("Please provide a product name and some features so the AI knows what to write about.")

        with tab5:
            st.subheader("Point of Source (POS+)")
            st.caption("Catalog inventory with images, pricing, and tags for instant retrieval during live sessions.")

            # Main Ingestion Container
            with st.container(border=True):
                col_capture, col_form = st.columns([1, 1], gap="medium")

                # Distinct Bordered Container 1
                with col_capture:
                    with st.container(border=True):
                        st.markdown("##### 📸 Capture Item to be logged")
                        camera_photo = st.camera_input("Take Photo", key="vault_cam")
                        uploaded_photo = st.file_uploader("Or upload high-res image", type=["jpg", "png", "jpeg"], key="vault_upload")
                        active_photo = camera_photo or uploaded_photo

                # Distinct Bordered Container 2
                with col_form:
                    with st.container(border=True):
                        st.markdown("##### 📝 Item Details")
                
                        category = st.selectbox("Category", ["Choker Set", "Earrings", "Bangles", "Polki", "Kundan", "Other"], key="vault_cat")

                        # Stock Quantity Input
                        c1, c2 = st.columns(2)
                        with c1:
                            sourcing_price = st.number_input("Sourcing Price (₹)", min_value=0.0, step=50.0, value=500.0, key="vault_price")
                        with c2:
                            stock_qty = st.number_input("Stock Quantity", min_value=1, step=1, value=1, key="vault_qty")
                            
                        raw_tags = st.text_input("Additional Tags (to be used in case of low network connectivity)", placeholder="e.g., Mint Green, Pearl Drops", key="vault_tags")

                        combined_tags = f"{category}, {raw_tags}" if raw_tags else category
                
                        st.divider()
                        st.markdown("##### 💡 Selling Prices")
                        st.caption("Edit these calculated targets to save custom prices to the vault.")
                
                        p_col1, p_col2, p_col3 = st.columns(3)
                        custom_std = p_col1.number_input("Standard", value=float(sourcing_price * 1.8), step=10.0)
                        custom_vip = p_col2.number_input("VIP", value=float(sourcing_price * 1.5), step=10.0)
                        custom_clr = p_col3.number_input("Clearance", value=float(sourcing_price * 1.2), step=10.0)

                        generated_sku = f"JK-{int(time.time())}-{uuid.uuid4().hex[:4].upper()}"
                
                        save_btn = st.button("💾 Save to Vault", type="primary", use_container_width=True, key="save_vault_btn")

            if save_btn and active_photo:
                with st.spinner("Compressing image & updating Vault..."):
                    raw_bytes = active_photo.getvalue()
                    compressed_bytes = compress_image(raw_bytes)
                    cdn_url = upload_to_cloudinary(compressed_bytes, generated_sku)

                    if "🚨" not in cdn_url:
                        # FIX: Now passing all 7 variables to the backend
                        is_saved = save_to_sourcing_vault(
                            generated_sku, 
                            sourcing_price, 
                            combined_tags, 
                            cdn_url, 
                            custom_std, 
                            custom_vip, 
                            custom_clr,
                            stock_qty
                        )
                
                        if is_saved:
                            st.toast(f"✅ Saved {generated_sku} to Vault!", icon="🎉")
                        else:
                            st.error("⚠️ Failed to update Google Sheet ledger.")
                    else:
                        st.error(cdn_url)

            # 3. Recently Cataloged Mini-Gallery
            
            st.divider()
            st.markdown("##### 🕒 Recently Cataloged Inventory")
            vault_df = load_sourcing_vault()
            if not vault_df.empty:
                recent_items = vault_df.tail(4).iloc[::-1] # Get last 4 items
                g_cols = st.columns(len(recent_items))
                for idx, (_, item) in enumerate(recent_items.iterrows()):
                    with g_cols[idx]:
                        st.image(item['image_url'], use_container_width=True)
                        st.caption(f"**{item['Item_SKU']}**\nCost: ₹{item['Sourcing_Price']}")

        with tab6:
            st.subheader("🔴 Live Broadcast Assistant")
            st.caption("Scan items on camera or run manual searches to instantly pull sourcing costs and quotes.")

            # Low-Network Toggle Switch
            low_net_mode = st.toggle("📶 Low-Network Mode (Disable Camera)", key="low_net_toggle")

            vault_df = load_sourcing_vault()
            match = None
            live_bytes = None

            with st.container(border=True):
                if not low_net_mode:
                    live_camera = st.camera_input("📸 Scan Jewelry Piece", key="live_match_cam")
                    if live_camera:
                        live_bytes = live_camera.getvalue()
                else:
                    st.info("📶 Low-network mode active. Camera disabled to save bandwidth.")
                    live_camera = None

                manual_search = st.text_input(
                    "🔍 Manual Search Fallback", 
                    placeholder="Search by color, type, or style (e.g., 'Mint Green Choker')...",
                    key="manual_match_input"
                )

            # Execution Logic
            if live_camera and not manual_search:
                with st.spinner("🧠 AI Analyzing visual attributes..."):
                    ai_tags = analyze_live_item(live_bytes)
                    if "🚨" not in ai_tags:
                        st.info(f"🧠 **AI Visual Analysis:** `{ai_tags}`")
                        match = find_vault_match(ai_tags, vault_df)
                    else:
                        st.error(ai_tags)

            elif manual_search:
                match = find_vault_match(manual_search, vault_df)

            # Output Presentation Card
            if match is not None:
                st.divider()
                st.markdown(
                    '<div style="background-color:#e8f5e9; padding:8px 16px; border-radius:8px; border:1px solid #c8e6c9;">'
                    '<span style="color:#2e7d32; font-weight:bold; font-size:16px;">🟢 Match Confirmed in Vault</span>'
                    '</div>', 
                    unsafe_allow_html=True
                )
                st.write("")

                with st.container(border=True):
                    # Side-by-Side Visual Verification
                    col_live, col_vault, col_pricing = st.columns([1, 1, 1.5], gap="large")

                    with col_live:
                        st.markdown("**Scanned Feed**")
                        if live_bytes:
                            st.image(live_bytes, use_container_width=True)
                        else:
                            st.caption("Manual Search Mode")

                    with col_vault:
                        st.markdown("**Database Record**")
                        st.image(match['image_url'], use_container_width=True)
                        st.caption(f"SKU: `{match['Item_SKU']}`")

                    with col_pricing:

                        with col_pricing:
                            cost_price = float(match['Sourcing_Price'])
                            st.metric("Sourcing Cost", f"₹{cost_price:,.2f}")
                            st.caption(f"**Tags:** {match['tags']}")
                            st.divider()

                            st.markdown("##### 📋 Tap to Copy Quotes")
            
                            def safe_quote(col_name, multiplier):
                                val = match.get(col_name)
                                import pandas as pd
                                # If cell is missing, NaN, or a blank string, fallback to math
                                if pd.isna(val) or str(val).strip() == "":
                                    return cost_price * multiplier
                                try:
                                    return float(val)
                                except ValueError:
                                    return cost_price * multiplier

                            # Safely parse the quotes
                            std_quote = safe_quote('Standard_Price', 1.8)
                            vip_quote = safe_quote('VIP_Price', 1.5)
                            clr_quote = safe_quote('Clearance_Price', 1.2)

                            c1, c2, c3 = st.columns(3)
                            with c1:
                                st.caption("Standard")
                                st.code(f"₹{std_quote:,.0f}", language="markdown")
                            with c2:
                                st.caption("VIP Client")
                                st.code(f"₹{vip_quote:,.0f}", language="markdown")
                            with c3:
                                st.caption("Clearance")
                                st.code(f"₹{clr_quote:,.0f}", language="markdown")

            elif (live_camera or manual_search) and match is None:
                st.warning("⚠️ No matching item found in the Sourcing Vault. Verify search tags or check inventory log.")

        with tab7:
            st.subheader("🛒 Point of Sale (POS)")
            st.caption("Log transactions securely. Line items will automatically sync to analytics and invoicing.")
            
            with st.container(border=True):
                st.markdown("##### 👤 Client Information")
                c1, c2 = st.columns(2)
                
                with c1:
                    formal_name = st.text_input("Formal Name (For Invoice)", placeholder="e.g., Priya Sharma", key="pos_name")
                with c2:
                        social_handle = st.text_input("Instagram / Social Handle", placeholder="e.g., @priya_styles", key="pos_handle")
            
                st.divider()
                st.markdown("##### 📦 Sold Items")
                st.info("Will be used for Billing")
                
                # Initialize an empty dataframe in session state for the dynamic table
                if 'pos_items' not in st.session_state:
                    st.session_state.pos_items = pd.DataFrame([
                        {"Item_SKU": "", "Category": "Choker Set", "Quantity": 1, "Unit Price (₹)": 0.0}
                    ])
                
                # Dynamic Data Editor
                categories = ["Choker Set", "Earrings", "Bangles", "Polki", "Kundan", "Ring", "Other"]
                edited_df = st.data_editor(
                    st.session_state.pos_items,
                    column_config={
                        "Item_SKU": st.column_config.TextColumn("𝗜𝘁𝗲𝗺 𝗦𝗞𝗨 (Required for Stock Maintenance)"),
                        "Category": st.column_config.SelectboxColumn("𝗖𝗮𝘁𝗲𝗴𝗼𝗿𝘆", options=categories, required=True),
                        "Quantity": st.column_config.NumberColumn("𝗤𝘂𝗮𝗻𝘁𝗶𝘁𝘆", min_value=1, step=1, required=True),
                        "Unit Price (₹)": st.column_config.NumberColumn("𝗨𝗻𝗶𝘁 𝗣𝗿𝗶𝗰𝗲 (₹)", min_value=0.0, format="₹%.2f", required=True)
                    },
                num_rows="dynamic",
                use_container_width=True,
                key="pos_data_editor"
                )
            
                # Auto-calculate totals based on the table
                calc_pieces = int(edited_df["Quantity"].sum())
                calc_revenue = float((edited_df["Quantity"] * edited_df["Unit Price (₹)"]).sum())
                
                st.divider()
                st.markdown("##### 💰 Financials")
                f1, f2, f3 = st.columns(3)
                
                with f1:
                    cost_price = st.number_input("Total Sourcing Cost (₹)", min_value=0.0, step=50.0, key="pos_cost")
                with f2:
                        courier_charge = st.number_input("Courier Charge Paid (₹)", min_value=0.0, step=10.0, key="pos_courier")
                with f3:
                    final_received = st.number_input("Final Amount Received (₹)", value=calc_revenue, min_value=0.0, step=50.0, key="pos_final")
                
                payment_status = st.selectbox("Payment Status", ["Paid Online", "Cash on Delivery", "Pending"], key="pos_status")
            
                save_sale_btn = st.button("💾 Finalize Transaction", type="primary", use_container_width=True, key="save_pos_btn")

                # Execution Logic
                if save_sale_btn:
                    if not formal_name or not social_handle:
                        st.error("⚠️ Please provide both the Formal Name and Social Handle.")
                    elif calc_pieces == 0:
                        st.error("⚠️ Please add at least one item to the cart.")
                    else:
                        with st.spinner("Logging transaction to database..."):
                            # Call the backend function to serialize JSON and write to Google Sheets
                            success = log_new_sale(
                                formal_name=formal_name,
                                handle=social_handle,
                                line_items_df=edited_df,
                                total_pieces=calc_pieces,
                                total_cost=cost_price,
                                courier=courier_charge,
                                amount_paid=final_received,
                                payment_status=payment_status
                            )
                        
                            if success:
                                st.success(f"✅ Transaction logged for {formal_name}! Total Pieces: {calc_pieces}")

                                # 🚀 FIX: Gracefully reset the cart instead of deleting the key
                                st.session_state.pos_items = pd.DataFrame([
                                {"Item_SKU": "", "Category": "Choker Set", "Quantity": 1, "Unit Price (₹)": 0.0}
                            ])
                                st.cache_data.clear()
                                st.rerun()

    except Exception as e:
        st.error(f"Database Connection Error: {e}")

if __name__ == "__main__":
    if check_password():
        main()