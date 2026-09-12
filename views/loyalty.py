import streamlit as st
from engines.crm import engine_vip_loyalty

def render_loyalty(df_sales):
    st.subheader("Client Lifetime Value (CLV) Screener")
    st.markdown("Use this to prioritize DMs and offer exclusive sneak peeks before live sessions.")
    
    if not df_sales.empty and 'handle' in df_sales.columns:
        vip_data = engine_vip_loyalty(df_sales)
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("#### 🏆 Top High-Value Clients")
            
            for index, row in vip_data.head(10).iterrows():
                with st.container(border=True):
                    # MOBILE FIX: Adjust ratio to 3:1 to give long handles more breathing room
                    card_col1, card_col2 = st.columns([3, 1])
                    
                    with card_col1:
                        # MOBILE FIX: Truncate handles longer than 25 characters to prevent visual overflow
                        raw_handle = str(row['handle'])
                        display_handle = raw_handle if len(raw_handle) <= 25 else raw_handle[:22] + "..."
                        
                        st.markdown(f"**👤 {display_handle}**")
                        
                        if row['Client Status'] == 'VIP':
                            st.caption("🌟 VIP Status")
                        else:
                            st.caption("✅ Active Client")
                            
                    with card_col2:
                        st.markdown(f"**₹{row['Lifetime_Spend']:,.0f}**")
                        st.caption(f"🛍️ {row['Total_Orders']} Orders")
                
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