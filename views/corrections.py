import streamlit as st
from data.repository import BusinessRepository

def render_corrections():
    st.subheader("🛠️ Recent Transactions")
    st.markdown("Select the transaction to safely correct amounts, names, or payment statuses.")

    df_sales = BusinessRepository.get_sales_data()

    if not df_sales.empty and 'Order_ID' in df_sales.columns:
        # Filter out rows with blank Order IDs
        valid_orders = df_sales[df_sales['Order_ID'].astype(str).str.strip() != ""]

        if not valid_orders.empty:
            # Sort by most recent first
            valid_orders = valid_orders.iloc[::-1].copy()

            # Create a clean display string for selection
            valid_orders['Display'] = (
                valid_orders['Order_ID'].astype(str) + " - " + 
                valid_orders['Client Formal Name'].astype(str) + " (₹" + 
                valid_orders['Total Amount Client Paid You'].astype(str) + ")"
            )

            selected_display = st.selectbox("Select Order to Correct", options=valid_orders['Display'].tolist())

            if selected_display:
                # Extract the exact row based on selection
                selected_row = valid_orders[valid_orders['Display'] == selected_display].iloc[0]
                order_id = str(selected_row['Order_ID'])

                with st.form(key=f"edit_form_{order_id}"):
                    st.markdown(f"**Editing Order ID:** `{order_id}`")
                    st.caption(f"Timestamp of Sale: {selected_row.get('Timestamp', 'N/A')}")

                    new_client_name = st.text_input(
                        "Client Formal Name", 
                        value=str(selected_row.get('Client Formal Name', ''))
                    )
                    
                    new_amount = st.number_input(
                        "Total Amount Client Paid (₹)", 
                        min_value=0.0, 
                        step=50.0, 
                        value=float(selected_row.get('Total Amount Client Paid You', 0.0))
                    )
                    
                    current_status = str(selected_row.get('Payment Status', 'Paid Online'))
                    status_options = ["Paid Online", "COD Pending", "COD Completed", "Cancelled"]
                    status_idx = status_options.index(current_status) if current_status in status_options else 0
                    
                    new_status = st.selectbox("Payment Status", options=status_options, index=status_idx)

                    submit_update = st.form_submit_button("💾 Save Corrections", type="primary", use_container_width=True)

                    if submit_update:
                        with st.spinner("Updating secure database..."):
                            result = BusinessRepository.update_transaction(order_id, new_amount, new_status, new_client_name)
                            if result is True:
                                st.toast("✅ Transaction successfully updated!", icon="🎉")
                                st.cache_data.clear() # Clear cache to fetch updated sheet data instantly
                                st.rerun()
                            else:
                                st.error(f"⚠️ Failed to update database: {result}")
        else:
            st.info("No valid orders found to edit.")
    else:
        st.warning("Sales database is empty or missing Order_ID column.")