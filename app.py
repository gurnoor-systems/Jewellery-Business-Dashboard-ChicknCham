import streamlit as st
from data.ingestion import load_data
from engines.financials import engine_cost_profitability
from engines.crm import engine_vip_loyalty
from engines.invoicing import engine_automated_invoicing

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
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Realized Revenue", f"₹{sales:,.0f}")
                col2.metric("True Net Profit", f"₹{profit:,.0f}")
                col3.metric("Top Performer", top_item)
                col4.metric("⚠️ 45-Day Dead Stock", f"₹{dead_capital:,.0f}", delta="Capital Trapped", delta_color="inverse")
                
                st.divider()
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
            
    except Exception as e:
        st.error(f"Database Connection Error: {e}")

if __name__ == "__main__":
    if check_password():
        main()