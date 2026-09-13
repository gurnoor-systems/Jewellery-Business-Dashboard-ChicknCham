import streamlit as st
import pandas as pd
from sqlalchemy import text
from data.repository import BusinessRepository

def render_mirror():
    st.subheader("🪞 Master Database Mirror")
    st.caption("Live read/write access to the core sales ledger. Optimized for zero-latency by loading only the 50 most recent records by default.")

    search_query = st.text_input(
        "🔍 Search Historical Records", 
        placeholder="Type a Client Name or Instagram Handle (e.g., Priya or @priya_styles)"
    )

    # 1. LATENCY OPTIMIZATION: Delegating heavy sorting and filtering to PostgreSQL
    conn = st.connection("postgresql", type="sql")
    
    with st.spinner("Querying secure ledger..."):
        if search_query:
            sql = text("""
                SELECT id, created_at, formal_name, handle, amount_paid, payment_status 
                FROM sales 
                WHERE formal_name ILIKE :search OR handle ILIKE :search
                ORDER BY created_at DESC LIMIT 50
            """)
            df = conn.query(sql, params={"search": f"%{search_query.strip()}%"})
        else:
            sql = text("""
                SELECT id, created_at, formal_name, handle, amount_paid, payment_status 
                FROM sales 
                ORDER BY created_at DESC LIMIT 50
            """)
            df = conn.query(sql)

    if not df.empty:
        st.markdown("##### 📝 Editable Sales Ledger")
        
        # 2. UI RENDERER: Native Data Editor
        edited_df = st.data_editor(
            df,
            use_container_width=True,
            hide_index=True,
            num_rows="fixed", 
            disabled=["id", "created_at"], 
            column_config={
                "id": st.column_config.TextColumn("ID"),
                "created_at": st.column_config.DatetimeColumn("Date Logged", format="D MMM YYYY, h:mm a"),
                "formal_name": st.column_config.TextColumn("Client Name", required=True),
                "handle": st.column_config.TextColumn("Social Handle", required=True),
                "amount_paid": st.column_config.NumberColumn("Amount Paid (₹)", min_value=0.0, format="₹%.2f"),
                "payment_status": st.column_config.SelectboxColumn("Status", options=["Paid Online", "Cash on Delivery", "Pending", "Refunded"])
            },
            key="master_ledger_editor"
        )
        
        # 3. ATOMIC STATE TRACKING
        editor_state = st.session_state.get("master_ledger_editor", {})
        if len(editor_state.get("edited_rows", {})) > 0:
            st.warning("⚠️ Uncommitted changes detected in the grid.")
            
            if st.button("💾 Commit Changes to Database", type="primary", use_container_width=True):
                with st.spinner("Securing updates..."):
                    success_count = 0
                    
                    for row_idx, changes_dict in editor_state["edited_rows"].items():
                        target_id = int(df.iloc[row_idx]["id"])
                        new_name = str(edited_df.iloc[row_idx]["formal_name"]).strip()
                        new_handle = str(edited_df.iloc[row_idx]["handle"]).strip()
                        new_amount = float(edited_df.iloc[row_idx]["amount_paid"])
                        new_status = str(edited_df.iloc[row_idx]["payment_status"])
                        
                        if BusinessRepository.update_transaction(
                            order_id=target_id,
                            client_name=new_name,
                            amount=new_amount,
                            status=new_status,
                            handle=new_handle
                        ):
                            success_count += 1
                    
                    if success_count > 0:
                        st.success(f"✅ Successfully updated {success_count} record(s)!")
                        st.cache_data.clear()
                        st.rerun()
    else:
        st.info("No records found matching that search.")