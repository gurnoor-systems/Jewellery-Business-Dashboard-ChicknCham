import streamlit as st
import pandas as pd
from data.sales import log_new_sale

def render_pos():
    st.subheader("🛒 Point of Sale (POS)")
    st.caption("Log transactions securely. Line items will automatically sync to analytics and invoicing.")
    
    # Initialize Cart in Session State
    if 'pos_cart' not in st.session_state:
        st.session_state.pos_cart = []
    
    with st.container(border=True):
        st.markdown("##### 👤 Client Information")
        c1, c2 = st.columns(2)
        
        with c1:
            formal_name = st.text_input("Formal Name (For Invoice)", placeholder="e.g., Priya Sharma", key="pos_name")
        with c2:
            social_handle = st.text_input("Instagram / Social Handle", placeholder="e.g., @priya_styles", key="pos_handle")
    
    st.divider()
    
    # UPGRADE: Form blocks the 5-7 second gray screen refresh!
    with st.form("add_item_form", clear_on_submit=True):
        st.markdown("##### ➕ Add Item to Order")
        
        item_sku = st.text_input("Item SKU", placeholder="e.g. JK-12345")
        category = st.selectbox("Category", ["Choker Set", "Earrings", "Bangles", "Polki", "Kundan", "Ring", "Other"])
        custom_details = st.text_input("Custom Details (Optional)")
        
        qty_col, source_col, price_col = st.columns(3)
        with qty_col:
            qty = st.number_input("Quantity", min_value=1, step=1)
        with source_col:
            source_price = st.number_input("Source Price (₹)", min_value=0.0, step=100.0)
        with price_col:
            Selling_price = st.number_input("Selling Price (₹)", min_value=0.0, step=100.0)
            
        add_to_cart = st.form_submit_button("🛒 Add to Cart", use_container_width=True)
        
        if add_to_cart:
            st.session_state.pos_cart.append({
                "Item_SKU": item_sku,
                "Category": category,
                "Custom Details": custom_details,
                "Quantity": qty,
                "Source Price (₹)": source_price,
                "Selling Price (₹)": Selling_price
            })
            st.success("Item added to cart!")

    calc_pieces = 0
    calc_cost = 0.0
    calc_revenue = 0.0
    
    if st.session_state.pos_cart:
        st.markdown("##### 🛍️ Current Cart")
        for idx, item in enumerate(st.session_state.pos_cart):
            with st.container(border=True):
                # Asymmetrical columns to mimic a native mobile app cart
                cart_col1, cart_col2 = st.columns([5, 1])
                
                with cart_col1:
                    st.markdown(f"**{item['Category']}** | `{item['Item_SKU']}`")
                    if item['Custom Details']:
                        st.caption(f"Details: {item['Custom Details']}")

                    # Displaying both prices in the cart for clarity
                    sell_p = item.get('Selling Price (₹)', 0)
                    src_p = item.get('Source Price (₹)', 0)
                    st.markdown(f"Qty: **{item['Quantity']}** | Sell: **₹{sell_p:,.2f}** | Cost: **₹{src_p:,.2f}**")
                    
                with cart_col2:
                    # Push the button down slightly so it centers vertically next to the text
                    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
                    if st.button("❌", key=f"del_cart_item_{idx}", help="Delete this item"):
                        st.session_state.pos_cart.pop(idx)
                        st.rerun()
            
            calc_pieces += item['Quantity']
            calc_cost += (item['Quantity'] * item.get('Source Price (₹)', 0))
            calc_revenue += (item['Quantity'] * item['Selling Price (₹)'])
            
        if st.button("🗑️ Clear Cart", key="clear_cart_btn"):
            st.session_state.pos_cart = []
            st.rerun()

    st.divider()
    st.markdown("##### 💰 Financials & Checkout")
    f1, f2, f3 = st.columns(3)
    
    with f1:
        cost_price = st.number_input("Total Sourcing Cost (₹)", value=float(calc_cost), min_value=0.0, step=100.0, key="pos_cost")
    with f2:
        courier_charge = st.number_input("Courier Charge Paid (₹)", value=0.0, min_value=0.0, step=10.0, key="pos_courier")
    with f3:
        final_received = st.number_input("Final Amount Received (₹)", value=float(calc_revenue), min_value=0.0, step=100.0, key="pos_final")
    
    payment_status = st.selectbox("Payment Status", ["Paid Online", "Cash on Delivery", "Pending"], key="pos_status")

    save_sale_btn = st.button("💾 Finalize Transaction", type="primary", use_container_width=True, key="save_pos_btn")

    # Execution Logic
    if save_sale_btn:
        if not formal_name or not social_handle:
            st.error("⚠️ Please provide both the Formal Name and Social Handle.")
        elif len(st.session_state.pos_cart) == 0:
            st.error("⚠️ Please add at least one item to the cart.")
        else:
            with st.spinner("Logging transaction to database..."):
                # Convert the session state list of dictionaries back to a DataFrame for the backend
                pos_df = pd.DataFrame(st.session_state.pos_cart)
                
                success = log_new_sale(
                    formal_name=formal_name,
                    handle=social_handle,
                    line_items_df=pos_df,
                    total_pieces=calc_pieces,
                    total_cost=cost_price,
                    courier=courier_charge,
                    amount_paid=final_received,
                    payment_status=payment_status
                )
            
                if success:
                    st.success(f"✅ Transaction logged for {formal_name}! Total Pieces: {calc_pieces}")
                    # Clear the cart memory instantly
                    st.session_state.pos_cart = []
                    st.cache_data.clear()
                    st.rerun()