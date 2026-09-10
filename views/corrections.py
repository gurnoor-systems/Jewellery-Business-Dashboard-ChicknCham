import streamlit as st
from data.repository import BusinessRepository

def render_corrections():
    st.subheader("🛠️ Recent Transactions")
    st.markdown("Select the transaction to correct amounts, names, or payment statuses.")

    df_sales = BusinessRepository.get_sales_data()

    # Update to use the new 'id' column instead of 'Order_ID'
    if not df_sales.empty and 'id' in df_sales.columns:
        # Filter out rows with blank IDs safely
        valid_orders = df_sales[df_sales['id'].astype(str).str.strip() != ""].copy()

        if not valid_orders.empty:
            target_orders = valid_orders.tail(10).iloc[::-1].copy()
            st.caption("⚡ Showing the 10 most recent transactions for quick editing.")

            # Create a clean display string for selection using new column names
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
                    # Update to use the new 'created_at' column
                    st.caption(f"Timestamp of Sale: {selected_row.get('created_at', 'N/A')}")

                    # Consolidated and cleaned inputs using the exact PostgreSQL schema
                    new_client_name = st.text_input(
                        "Client Formal Name", 
                        value=str(selected_row.get('formal_name', ''))
                    )
                    
                    new_amount = st.number_input(
                        "Total Amount Client Paid (₹)", 
                        min_value=0.0, 
                        step=50.0, 
                        value=float(selected_row.get('amount_paid', 0.0))
                    )
                    
                    current_status = str(selected_row.get('payment_status', 'Paid Online'))
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
                                st.error(f"⚠️ Failed to update database: {result}")
        else:
            st.info("No valid orders found to edit.")
    else:
        st.warning("Sales database is empty or missing 'id' column.")