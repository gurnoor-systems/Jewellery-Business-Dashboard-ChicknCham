import streamlit as st
from data.ingestion import load_data
from engines.financials import engine_cost_profitability, generate_financial_charts, engine_cac_mom_growth
from engines.crm import engine_vip_loyalty
from engines.invoicing import engine_automated_invoicing
from engines.marketing import generate_instagram_captions

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
            value=1500.0,
            help="Enter any amount. Type directly or use arrows."
        )
        
    try:
        with st.spinner("Syncing secure database.."):
            df_sales, df_sourcing = load_data()
            
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Profitability Engine", 
            "👑 Loyalty Dashboard", 
            "🧾 Invoice Generator",
            "🎨 Marketing Content Generator"
        ])
        
        with tab1:
            st.subheader("Current Financial Health")
            if not df_sales.empty and not df_sourcing.empty:
                # 1. Run core calculations
                sales, profit, top_item, dead_capital = engine_cost_profitability(df_sales, df_sourcing)
                cac, new_clients, mom = engine_cac_mom_growth(df_sales, weekly_spend)

                # 2. Defensive Input Checks & Feedback
                if weekly_spend == 0:
                    st.info("🌱 Organic Growth")
                elif weekly_spend > 10_000_000:
                    st.error("🚨 The amount entered is exceptionally high (over ₹1 Cr). Please verify the value in the sidebar.")

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
                    ui_cac_label = "₹0 (Organic) 🌿" 
                    wa_cac_label = "₹0 (Organic)"
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
            
    except Exception as e:
        st.error(f"Database Connection Error: {e}")

if __name__ == "__main__":
    if check_password():
        main()