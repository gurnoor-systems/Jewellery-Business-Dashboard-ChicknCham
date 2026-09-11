import streamlit as st
import pandas as pd
from data.sales import log_new_sale
from data.repository import BusinessRepository
from data.sourcing import batch_deduct_inventory

# VIP Threshold Configuration
VIP_THRESHOLD = 3

def render_pos():
    st.subheader("🛒 Point of Sale (POS)")
    st.caption("Process new sales and log jewelry dispatch.")
    
    if 'pos_cart' not in st.session_state:
        st.session_state.pos_cart = []
        
    df_sales = BusinessRepository.get_sales_data()
    client_history = {}
    
    if not df_sales.empty and 'handle' in df_sales.columns:
        order_counts = df_sales['handle'].value_counts().to_dict()
        for handle, count in order_counts.items():
            if pd.isna(handle) or str(handle).strip() == "":
                continue
            if count >= VIP_THRESHOLD:
                display_name = f"👑 {handle} (VIP: {count} Orders)"
            else:
                display_name = f"👤 {handle} ({count} Orders)"
            client_history[display_name] = handle
    
    with st.container(border=True):
        st.markdown("##### 👤 Client Information")
        known_clients = list(client_history.keys())
        selected_client_display = st.selectbox(
            "Search Past Clients here", 
            options=known_clients, 
            index=None, 
            placeholder="🔍 Type to search past clients..."
            )
        
        auto_handle = ""
        auto_name = ""
        
        if selected_client_display:
            auto_handle = client_history[selected_client_display]
            past_records = df_sales[df_sales['handle'] == auto_handle]
            if not past_records.empty and 'formal_name' in past_records.columns:
                auto_name = str(past_records.iloc[0]['formal_name'])
                
            if "👑" in selected_client_display:
                st.success(f"🌟 **VIP Customer Alert!** They have placed {selected_client_display.split('(')[1].replace(')', '')}. Consider adding a free gift!")

        c1, c2 = st.columns(2)
        with c1:
            formal_name = st.text_input("Formal Name (For Invoice)", value=auto_name, placeholder="e.g., Priya Sharma", key="pos_name")
        with c2:
            social_handle = st.text_input("Instagram / Social Handle", value=auto_handle, placeholder="e.g., @priya_styles", key="pos_handle")
    
    st.divider()
    
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
            # STRICT BOUNDARY: Block whitespace-only SKUs
            if not str(item_sku).strip():
                st.error("⚠️ Item SKU is required and cannot be blank.")
            else:
                st.session_state.pos_cart.append({
                    "Item_SKU": str(item_sku).strip(),
                    "Category": str(category).strip(),
                    "Custom Details": str(custom_details).strip(),
                    "Quantity": int(qty),
                    "Source Price (₹)": round(float(source_price), 2),
                    "Selling Price (₹)": round(float(Selling_price), 2)
                })
                st.success("Item added to cart!")

    calc_pieces = 0
    calc_cost = 0.0
    calc_revenue = 0.0
    
    if st.session_state.pos_cart:
        st.markdown("##### 🛍️ Current Cart")
        for idx, item in enumerate(st.session_state.pos_cart):
            with st.container(border=True):
                cart_col1, cart_col2 = st.columns([5, 1])
                with cart_col1:
                    st.markdown(f"**{item['Category']}** | `{item['Item_SKU']}`")
                    if item['Custom Details']:
                        st.caption(f"Details: {item['Custom Details']}")
                    sell_p = item.get('Selling Price (₹)', 0)
                    src_p = item.get('Source Price (₹)', 0)
                    st.markdown(f"Qty: **{item['Quantity']}** | Sell: **₹{sell_p:,.2f}** | Cost: **₹{src_p:,.2f}**")
                with cart_col2:
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

    if save_sale_btn:
        # STRICT BOUNDARY: Block whitespace-only names/handles
        clean_name = str(formal_name).strip()
        clean_handle = str(social_handle).strip()
        
        if not clean_name or not clean_handle:
            st.error("⚠️ Please provide valid text for both the Formal Name and Social Handle.")
        elif len(st.session_state.pos_cart) == 0:
            st.error("⚠️ Please add at least one item to the cart.")
        else:
            with st.spinner("Logging transaction to database..."):
                pos_df = pd.DataFrame(st.session_state.pos_cart)
                
                # STRICT BOUNDARY: Round financials to 2 decimals to prevent float leak
                success = log_new_sale(
                    formal_name=clean_name,
                    handle=clean_handle,
                    line_items_df=pos_df,
                    total_pieces=calc_pieces,
                    total_cost=round(cost_price, 2),
                    courier=round(courier_charge, 2),
                    amount_paid=round(final_received, 2),
                    payment_status=payment_status
                )
            
                if success:
                    deduction_payload = [
                        {"sku": item["Item_SKU"], "qty": item["Quantity"]} 
                        for item in st.session_state.pos_cart
                    ]
                    inventory_updated = batch_deduct_inventory(deduction_payload)
                    
                    if inventory_updated:
                        st.success(f"✅ Sale logged and inventory depleted successfully!", icon="🎉")
                    else:
                        st.warning(f"✅ Sale logged, but inventory deduction failed. Please check stock manually.", icon="⚠️")
                        
                    st.info(f"Transaction logged for {clean_name}! Total Pieces: {calc_pieces}")
                    st.session_state.pos_cart = []
                    st.cache_data.clear()
                    st.rerun()