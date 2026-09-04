import time
import streamlit as st
import hashlib
from google import genai
import logging

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# Global AI Config
genai.configure(api_key=st.secrets["gemini"]["api_key"])

# Data Imports

from data.repository import BusinessRepository

# views Imports

from views.profitability import render_profitability
from views.loyalty import render_loyalty
from views.content_generator import render_content_generator
from views.catalog import render_catalog
from views.live_assistant import render_live_assistant 
from views.pos import render_pos
from views.invoice import render_invoice
from views.corrections import render_corrections

# SKU Unique Identifier Generator


# ==========================================
# 1. UI/UX & SYSTEM CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Chik n Cham by laddi 💎",
    page_icon="💎", 
    layout="wide"
)

# DEFENSE: Hide default Streamlit loading indicators and branding
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}

            /* Enlarge Button Touch Targets */
            .stButton > button {
                min-height: 48px;
                border-radius: 8px;
                font-weight: 600;
                transition: all 0.2s ease-in-out;
            }

            /* Enlarge Input Fields (Text, Number, Dropdowns) */
            input, .stSelectbox div[data-baseweb="select"] {
                min-height: 45px;
                border-radius: 6px;
            }
            
            /* Add Padding to Metric Cards */
            div[data-testid="stMetric"] {
                background-color: rgba(255, 255, 255, 0.05); 
                border-radius: 10px;
                padding: 15px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }

            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# ==========================================
# 2. SECURITY WALL and TTL TIMEOUT
# ==========================================

SESSION_TIMEOUT_SECONDS = 900  # 15 minutes of inactivity allowed

def check_password():
    """Returns True if the user entered the correct password and the session is fresh """
    
    # 1. Fast-Pass: If already authenticated, skip the checks and grant access immediately.
    # This completely protects the app from logging you out during PDF downloads.

    current_time = time.time()

    # 1. TTL Expiry Check
    if st.session_state.get("password_correct", False):
        last_active = st.session_state.get("last_active_time", current_time)

        # If idle time exceeds our limit, kill the session
        if (current_time - last_active) > SESSION_TIMEOUT_SECONDS:
            st.session_state["password_correct"] = False
            st.session_state["last_active_time"] = None
            st.warning("⏱️ Session timed out due to inactivity. Please log in again.")
            # Drops down to render the login UI below
        else:
            # Session is valid: update the timestamp to right now
            st.session_state["last_active_time"] = current_time
            return True
        
    # 2. Verification Logic
    def verify_password():
        input_pass = st.session_state.get("admin_password_input", "")
        input_hash = hashlib.sha256(input_pass.encode()).hexdigest()
        if input_hash == st.secrets["admin"]["password_hash"]:

            st.session_state["password_correct"] = True
            st.session_state["last_active_time"] = time.time() # Start the clock

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
    st.title("💎 Chik n Cham by laddi")
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

        st.divider()

        # ==========================================
        # 🛡️ CLIENT SAFETY NET: Instant Data Backup
        # ==========================================
        st.subheader("💾 Backup Your Records")
        st.caption("Download a complete, offline copy of all recorded sales anytime.")

        # Ensure we have data to export
        try:
            df_export = BusinessRepository.get_sales_data()
            if not df_export.empty:
                # Convert DataFrame to clean CSV format in memory
                csv_data = df_export.to_csv(index=False).encode('utf-8')
                
                st.download_button(
                    label="📥 Download Sales Backup (.csv)",
                    data=csv_data,
                    file_name="Sales_Backup_Records.csv",
                    mime="text/csv",
                    use_container_width=True,
                    help="Click to download your entire transaction history to your device."
                )
            else:
                st.info("No records available to export yet.")
        except Exception:
            st.caption("⚠️ Backup unavailable while offline.")

    try:
        with st.spinner("Syncing secure database.."):
            df_sales = BusinessRepository.get_sales_data()
            df_sourcing = BusinessRepository.get_sourcing_data()
                        
        tab1, tab2, tab4, tab5, tab6, tab7, tab3, tab8 = st.tabs([
            "📊 Profitability Dashboard", 
            "👑 Loyalty Dashboard", 
            "🎨 Content Generator",
            "🛒 Log Jewelery",
            "🔴 Jewelery info!",
            "🛒 Log a Sale",
            "🧾 Invoice",
            "🛠️ Recent Transactions"
        ])

        with tab1:
            render_profitability(df_sales, df_sourcing, weekly_spend)
            
        with tab2:
            render_loyalty(df_sales)

        with tab3:
            render_invoice(df_sales)

        with tab4:
            render_content_generator()

        with tab5:
            render_catalog()

        with tab6:
            render_live_assistant()

        with tab7:
            render_pos()
    
        with tab8:
            render_corrections()

    except Exception as e:

        logging.error(f"Critical System Failure: {e}", exc_info=True)
        st.error("⚠️ The system is currently busy or experiencing high traffic. Please try again in a few moments.")

if __name__ == "__main__":
    if check_password():
        main()