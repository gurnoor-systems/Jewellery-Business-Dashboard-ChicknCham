import streamlit as st
import pandas as pd
from data.repository import BusinessRepository

def render_corrections():
    st.subheader("🛠️ Recent Transactions")
    st.markdown("Select the transaction to correct amounts, names, or payment statuses.")

    # Memory Optimization: Fetch ONLY the last 10 rows and ONLY the required columns directly from SQL
    try:
        conn = st.connection("postgresql", type="sql")
        target_orders = conn.query("""
            SELECT id, formal_name, amount_paid, created_at, payment_status 
            FROM sales 
            ORDER BY id DESC 
            LIMIT 10;
        """, ttl="10m")
    except Exception as e:
        st.error("🚨 Failed to retrieve recent transactions.")
        target_orders = pd.DataFrame()

    if not target_orders.empty and 'id' in target_orders.columns:
        st.caption("⚡ Showing the 10 most recent transactions for quick editing.")

        # Create a clean display string for selection using exact PostgreSQL column names
        target_orders['Display'] = (
            target_orders['id'].astype(str) + " - " + 
            target_orders['formal_name'].astype(str) + " (₹" + 
            target_orders['amount_paid'].astype(str) + ")"
        )

        selected_display = st.selectbox("Select Order to Correct", options=target_orders['Display'].tolist())

        if selected_display:
            # Extract the exact row based on selection
            selected_row = target_orders[target_orders['Display'] == selected_display].iloc[0]
            order_id = str(selected_row['id'])

            with st.form(key=f"edit_form_{order_id}"):
                st.markdown(f"**Editing Order ID:** `{order_id}`")
                st.caption(f"Timestamp of Sale: {selected_row.get('created_at', 'N/A')}")

                # Consolidated and cleaned inputs
                new_client_name = st.text_input(
                    "Client Formal Name", 
                    value=str(selected_row.get('formal_name', '')).strip()
                )
                
                # Safely parse the amount
                try:
                    current_amount = float(selected_row.get('amount_paid', 0.0))
                except ValueError:
                    current_amount = 0.0
                    
                new_amount = st.number_input(
                    "Total Amount Client Paid (₹)", 
                    min_value=0.0, 
                    step=50.0, 
                    value=current_amount
                )
                
                current_status = str(selected_row.get('payment_status', 'Paid Online')).strip()
                status_options = ["Paid Online", "COD Pending", "COD Completed", "Cancelled"]
                status_idx = status_options.index(current_status) if current_status in status_options else 0
                
                new_status = st.selectbox("Payment Status", options=status_options, index=status_idx)

                submit_update = st.form_submit_button("💾 Save Corrections", type="primary", use_container_width=True)

                if submit_update:
                    with st.spinner("Updating secure database..."):
                        result = BusinessRepository.update_transaction(order_id, new_amount, new_status, new_client_name)
                        if result is True:
                            st.toast("✅ Transaction successfully updated!", icon="🎉")
                            st.cache_data.clear() 
                            st.rerun()
                        else:
                            st.error("⚠️ Failed to update database. Check logs for details.")
    else:
        st.warning("Sales database is empty or missing required columns.")