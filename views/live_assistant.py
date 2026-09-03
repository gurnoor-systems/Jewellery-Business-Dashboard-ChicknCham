import streamlit as st
import pandas as pd
from data.ingestion import load_sourcing_vault
from engines.live_match import analyze_live_item, find_vault_match

def render_live_assistant():
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
            uploaded_photo = st.file_uploader("Or upload a saved image", type=["jpg", "png", "jpeg"], key="live_match_upload")

            active_photo = live_camera or uploaded_photo

            if active_photo:
                live_bytes = active_photo.getvalue()
        else:
            st.info("📶 Low-network mode active. Camera disabled to save bandwidth.")
            active_photo = None
            live_bytes = None


        # MOBILE UPGRADE: Form blocks partial-word search freezing
        with st.form("manual_search_form"):
            manual_search = st.text_input(
                "🔍 Manual Search Fallback",
                placeholder="Search by color, type, or style (e.g., 'Mint Green Choker')...",
            )
            search_btn = st.form_submit_button("Search Vault", use_container_width=True)

    # Execution Logic
    if active_photo and not manual_search:
        with st.spinner("🧠 AI Analyzing visual attributes..."):
            ai_tags = analyze_live_item(live_bytes)
            if "🚨" not in ai_tags:
                st.info(f"🧠 **AI Visual Analysis:** `{ai_tags}`")
                match = find_vault_match(ai_tags, vault_df)
            else:
                st.error(ai_tags)

    # Execution is now tied to the search button being clicked
    elif search_btn and manual_search:
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
                    st.image(live_bytes, use_column_width=True)
                else:
                    st.caption("Manual Search Mode")

            with col_vault:
                st.markdown("**Database Record**")
                st.image(match['image_url'], use_column_width=True)
                st.caption(f"SKU: `{match['Item_SKU']}`")

            with col_pricing:
                cost_price = float(match['Sourcing_Price'])
                st.metric("Sourcing Cost", f"₹{cost_price:,.2f}")
                st.caption(f"**Tags:** {match['tags']}")
                st.divider()

                st.markdown("##### 📋 Tap to Copy Quotes")

                def safe_quote(col_name, multiplier):
                    val = match.get(col_name)
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

    elif (active_photo or manual_search) and match is None:
        st.warning("⚠️ No matching item found in the Sourcing Vault. Verify search tags or check inventory log.")