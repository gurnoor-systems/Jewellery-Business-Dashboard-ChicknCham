import streamlit as st
from engines.financials import engine_cost_profitability, engine_cac_mom_growth, generate_financial_charts

def render_profitability(df_sales, df_sourcing, weekly_spend):
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