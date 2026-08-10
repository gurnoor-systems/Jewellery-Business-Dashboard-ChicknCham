import time
import streamlit as st

# Data Imports

from data.ingestion import load_data, load_sourcing_vault
from data.storage import upload_to_cloudinary
from data.sourcing import compress_image, save_to_sourcing_vault

# Engine Imports

from engines.financials import engine_cost_profitability, generate_financial_charts, engine_cac_mom_growth
from engines.crm import engine_vip_loyalty
from engines.invoicing import engine_automated_invoicing
from engines.marketing import generate_instagram_captions
from engines.live_match import analyze_live_item, find_vault_match

# SKU Unique Identifier Generator

import uuid

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
    
    def password_entered():
        """Checks whether the password entered matches the secret."""
        if st.session_state["password"] == st.secrets["admin"]["password"]:
            st.session_state["password_correct"] = True
            # Delete the password from the session state for security
            del st.session_state["password"]  
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run: Show the password input
        st.markdown("### 🔐 Secure Login Required")
        st.text_input("Enter Admin Password", type="password", on_change=password_entered, key="password")
        return False
        
    elif not st.session_state["password_correct"]:
        # Incorrect password: Show input and error message
        st.markdown("### 🔐 Secure Login Required")
        st.text_input("Enter Admin Password", type="password", on_change=password_entered, key="password")
        st.error("🚫 Access Denied: Incorrect Password")
        return False
        
    else:
        # Password correct: Grant access
        return True

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
            
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 Profitability Engine", 
            "👑 Loyalty Dashboard", 
            "🧾 Invoice Generator",
            "🎨 Marketing Content Generator",
            "📸 Jewelery Vault",
            "🔴 LIVE MATCH"
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
            st.markdown("Use this intelligence to prioritize DMs and offer exclusive sneak peeks before live sessions.")
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
                    st.info("Message the top 3 clients on this list whenever the new stock arrives. "
                    "Converting these existing buyers cost zero in marketing.")

            else:
                st.warning("No sales data available yet to generate VIP list.")
            
        with tab3:
            st.subheader("🧾 Invoice Generator")
            st.markdown("Generate professional PDF receipts for your most recent cleared orders.")
            df_valid_sales = df_sales[df_sales['Payment Status'].isin(['Paid (UPI/Bank)', 'COD (Pending)'])].copy()
            
            if not df_valid_sales.empty:
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
                            pdf_bytes = engine_automated_invoicing(row)
                            st.download_button(
                                label="⬇️ Download PDF",
                                data=pdf_bytes,
                                file_name=f"ChickNCham_Receipt_{client}.pdf",
                                mime="application/pdf",
                                key=f"btn_{index}"
                            )
            else:
                st.info("No recent valid orders found to invoice.")
        
        with tab4:
            st.subheader("✨ AI Caption Generator")
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
                        st.markdown(generated_text)
                else:
                    st.warning("Please provide a product name and some features so the AI knows what to write about.")

        with tab5:
            st.subheader("📸 Mobile Sourcing Vault")
            st.caption("Catalog inventory on sourcing trips with instant price previews and automatic cloud sync.")

            # Main Ingestion Container
            with st.container(border=True):
                col_capture, col_form = st.columns([1, 1], gap="medium")

                # Distinct Bordered Container 1
                with col_capture:
                    with st.container(border=True):
                        st.markdown("##### 📸 Capture Media")
                        camera_photo = st.camera_input("Take Photo", key="vault_cam")
                        uploaded_photo = st.file_uploader("Or upload high-res image", type=["jpg", "png", "jpeg"], key="vault_upload")
                        active_photo = camera_photo or uploaded_photo

                # Distinct Bordered Container 2
                with col_form:
                    with st.container(border=True):
                        st.markdown("##### 📝 Item Details")
                
                        category = st.selectbox("Category", ["Choker Set", "Earrings", "Bangles", "Polki", "Kundan", "Other"], key="vault_cat")
                        sourcing_price = st.number_input("Sourcing Price (₹)", min_value=0.0, step=50.0, value=500.0, key="vault_price")
                        raw_tags = st.text_input("Additional Tags", placeholder="e.g., Mint Green, Pearl Drops", key="vault_tags")
                        combined_tags = f"{category}, {raw_tags}" if raw_tags else category
                
                        st.divider()
                        st.markdown("##### 💡 Custom Selling Prices")
                        st.caption("Edit these calculated targets to save custom prices to the vault.")
                
                        p_col1, p_col2, p_col3 = st.columns(3)
                        custom_std = p_col1.number_input("Standard", value=float(sourcing_price * 1.8), step=10.0)
                        custom_vip = p_col2.number_input("VIP", value=float(sourcing_price * 1.5), step=10.0)
                        custom_clr = p_col3.number_input("Clearance", value=float(sourcing_price * 1.2), step=10.0)

                        generated_sku = f"JK-{int(time.time())}-{uuid.uuid4().hex[:4].upper()}"
                
                        # Note: You will need to update data/sourcing.py to accept and save these 3 new custom price variables
                        save_btn = st.button("💾 Save to Vault", type="primary", use_container_width=True, key="save_vault_btn")

            if save_btn and active_photo:
                with st.spinner("Processing image, Please wait.."):
                    raw_bytes = active_photo.getvalue()
                    compressed_bytes = compress_image(raw_bytes)
                    cdn_url = upload_to_cloudinary(compressed_bytes, generated_sku)

                    if "🚨" not in cdn_url:
                        is_saved = save_to_sourcing_vault(generated_sku, sourcing_price, combined_tags, cdn_url)
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
                
                                # Pulls custom prices if they exist in the DB, otherwise falls back to math
                                std_quote = match.get('Standard_Price', cost_price * 1.8)
                                vip_quote = match.get('VIP_Price', cost_price * 1.5)
                                clr_quote = match.get('Clearance_Price', cost_price * 1.2)

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

    except Exception as e:
        st.error(f"Database Connection Error: {e}")

if __name__ == "__main__":
    if check_password():
        main()