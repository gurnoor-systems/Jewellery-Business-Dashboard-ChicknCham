import time
import uuid
import streamlit as st
import pandas as pd
from PIL import Image

from data.repository import BusinessRepository
from data.storage import upload_to_cloudinary, delete_from_cloudinary
from data.sourcing import compress_image, save_to_sourcing_vault, delete_from_sourcing_vault, restock_inventory
from engines.marketing import auto_tag_jewelry

# --- THE FROZEN CALLBACK ---
def commit_to_vault_callback(sku, price, qty, tags, category, img_bytes, custom_std, custom_vip, custom_clr, svfk):
    # 1. Hard Mutex Lock
    if st.session_state.get(f"submitting_{svfk}", False):
        return
    st.session_state[f"submitting_{svfk}"] = True
    
    try:
        # 2. HEAVY LIFTING: All execution happens here using the FROZEN arguments
        compressed_bytes = compress_image(img_bytes)
        cdn_url = upload_to_cloudinary(compressed_bytes, sku)

        if "🚨" not in cdn_url:
            combined_tags = f"{category}, {tags}" if tags else category
            
            final_std = custom_std if custom_std > 0 else float(price * 1.8)
            final_vip = custom_vip if custom_vip > 0 else float(price * 1.5)
            final_clr = custom_clr if custom_clr > 0 else float(price * 1.2)

            is_saved = save_to_sourcing_vault(
                sku, price, combined_tags, cdn_url, final_std, final_vip, final_clr, qty
            )
    
            if is_saved:
                # 3. Clean up the old dynamic keys before creating new ones
                for key in list(st.session_state.keys()):
                    if key.endswith(f"_{svfk}"):
                        del st.session_state[key]
                        
                st.session_state.vault_form_key += 1
                st.session_state["post_save_success"] = sku # Flag to trigger balloons in UI
            else:
                st.session_state["post_save_error"] = "⚠️ Failed to update database."
        else:
            st.session_state["post_save_error"] = cdn_url
            
    finally:
        # 4. Release the lock
        st.session_state[f"submitting_{svfk}"] = False


def render_catalog():
    st.subheader("Point of Source (POS+)")
    st.caption("Snap a photo. Let the AI do the heavy lifting.")

    if 'vault_form_key' not in st.session_state:
        st.session_state.vault_form_key = 0
    svfk = st.session_state.vault_form_key

    # Success/Error UI Triggers from the callback
    if "post_save_success" in st.session_state:
        sku_saved = st.session_state.pop("post_save_success")
        st.toast(f"✅ Saved {sku_saved}! Ready for next item.", icon="🎉")
        st.balloons()
        st.cache_data.clear()
        
    if "post_save_error" in st.session_state:
        st.error(st.session_state.pop("post_save_error"))

    if f"vault_cat_{svfk}" not in st.session_state:
        st.session_state[f"vault_cat_{svfk}"] = "Choker Set"
    if f"vault_tags_{svfk}" not in st.session_state:
        st.session_state[f"vault_tags_{svfk}"] = ""

    with st.container(border=True):
        st.markdown("##### 📸 Step 1: Capture Item")
        camera_photo = st.camera_input("Take Photo", key=f"vault_cam_{svfk}")
        uploaded_photo = st.file_uploader("Or upload from gallery", type=["jpg", "png", "jpeg"], key=f"vault_upload_{svfk}")
        active_photo = camera_photo or uploaded_photo

    if active_photo:
        current_img_id = getattr(active_photo, 'file_id', 'live_camera_feed')
        if st.session_state.get(f"analyzed_img_{svfk}") != current_img_id:
            with st.spinner("✨ AI is analyzing this piece..."):
                img = Image.open(active_photo)
                img.thumbnail((500, 500)) 
                
                ai_cat, ai_tags = auto_tag_jewelry(img)
                
                st.session_state[f"vault_cat_{svfk}"] = ai_cat
                st.session_state[f"vault_tags_{svfk}"] = ai_tags
                st.session_state[f"analyzed_img_{svfk}"] = current_img_id
                st.rerun()

        # NOTE: Removed clear_on_submit=True so we control exactly when the form resets
        with st.form(key=f"save_item_form_{svfk}"):
            st.markdown("##### 📝 Step 2: Verify & Price")
            st.info("The AI has pre-filled the category and tags. Just add the cost!")
            
            category = st.selectbox(
                "Category", 
                ["Choker Set", "Earrings", "Bangles", "Polki", "Kundan", "Ring", "Other"], 
                index=["Choker Set", "Earrings", "Bangles", "Polki", "Kundan", "Ring", "Other"].index(st.session_state[f"vault_cat_{svfk}"])
            )

            c1, c2 = st.columns(2)
            with c1:
                sourcing_price = st.number_input("Sourcing Price (₹)", min_value=0.0, step=50.0, value=500.0)
            with c2:
                stock_qty = st.number_input("Stock Quantity", min_value=1, step=1, value=1)

            raw_tags = st.text_input("Additional Tags", value=st.session_state[f"vault_tags_{svfk}"], placeholder="e.g., Mint Green, Pearl Drops")

            st.divider()

            with st.expander("⚙️ (click here) to Enter your Custom Pricing", expanded=False):
                st.caption("Leave at ₹0.0 to auto-calculate (1.8x, 1.5x, 1.2x). Enter a value to set a custom price.")
                p_col1, p_col2, p_col3 = st.columns(3)
                custom_std_override = p_col1.number_input("Standard (₹)", min_value=0.0, step=50.0, value=0.0)
                custom_vip_override = p_col2.number_input("VIP (₹)", min_value=0.0, step=50.0, value=0.0)
                custom_clr_override = p_col3.number_input("Clearance (₹)", min_value=0.0, step=50.0, value=0.0)

            generated_sku = f"JK-{int(time.time())}-{uuid.uuid4().hex[:4].upper()}"
            img_bytes = active_photo.getvalue()
    
            # CONCURRENCY FIX: Pass the frozen widget values explicitly into the callback
            st.form_submit_button(
                "💾 Save to Vault", 
                type="primary", 
                on_click=commit_to_vault_callback, 
                args=(
                    generated_sku, sourcing_price, stock_qty, raw_tags, 
                    category, img_bytes, custom_std_override, 
                    custom_vip_override, custom_clr_override, svfk
                ),
                use_container_width=True, 
                disabled=st.session_state.get(f"submitting_{svfk}", False)
            )

    # 3. Recently Cataloged Mini-Gallery
    st.divider()
    st.markdown("##### 🕒 Cataloged Inventory")

    vault_df = BusinessRepository.get_sourcing_data()
    if not vault_df.empty:
        col_filt1, col_filt2 = st.columns([1.5, 1])
        with col_filt1:
            filter_cat = st.selectbox(
                "Filter", 
                ["All", "Choker Set", "Earrings", "Bangles", "Polki", "Kundan", "Ring", "Other"],
                key="gallery_filter",
                label_visibility="collapsed"
            )
        with col_filt2:
            hide_sold_out = st.toggle("Hide Sold Out", value=True)

        display_df = vault_df.copy()
        display_df['Stock_Quantity'] = pd.to_numeric(display_df.get('Stock_Quantity', pd.Series(dtype=float)), errors='coerce').fillna(0)
        
        if hide_sold_out:
            display_df = display_df[display_df['Stock_Quantity'] > 0]

        if filter_cat != "All":
            display_df = display_df[display_df['tags'].astype(str).str.contains(filter_cat, case=False, na=False)]

        recent_items = display_df.tail(6).iloc[::-1]  
        
        if not recent_items.empty:
            grid_cols = st.columns(2)
            for idx, (_, item) in enumerate(recent_items.iterrows()):
                with grid_cols[idx % 2]:
                    with st.container(border=True):
                        img_val = item.get('image_url')

                        if pd.notna(img_val) and str(img_val).strip() != "" and str(img_val).strip().lower() != "none":
                            st.image(str(img_val).strip(), use_column_width=True)

                        sku_val = item.get('Item_SKU', 'N/A')
                        st.code(sku_val, language=None)
                        
                        current_stock = int(item.get('Stock_Quantity', 0))
                        if current_stock >= 3:
                            st.markdown(f"**🟢 In Stock ({current_stock})**")
                        elif current_stock > 0:
                            st.markdown(f"**🟡 Low Stock ({current_stock})**")
                        else:
                            st.markdown(f"**🔴 SOLD OUT**")
                        
                        cost = item.get('Sourcing_Price', 0)
                        st.caption(f"Cost: **₹{float(cost):,.0f}**")
                        tags = item.get('tags', '')
                        if tags:
                            st.caption(f"🏷️ {tags}")

                        with st.expander("📦 Restock Item"):
                            r_col1, r_col2 = st.columns([2, 3])
                            with r_col1:
                                add_qty = st.number_input("Qty", min_value=1, step=1, value=1, key=f"add_qty_{sku_val}_{idx}")
                            with r_col2:
                                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                                if st.button("➕ Confirm", key=f"restock_btn_{sku_val}_{idx}", use_container_width=True):
                                    with st.spinner("Restocking..."):
                                        if restock_inventory(sku_val, add_qty):
                                            st.toast(f"✅ {sku_val} restocked by {add_qty}!", icon="📦")
                                            st.cache_data.clear() 
                                            st.rerun()
                                        else:
                                            st.error("⚠️ Failed to update database.")

                        if st.button("🗑️ Delete", key=f"del_vault_{sku_val}_{idx}", use_container_width=True):
                            with st.spinner("Deleting from Cloud & Database..."):
                                cloud_cleared = delete_from_cloudinary(sku_val)
                                sheet_cleared = delete_from_sourcing_vault(sku_val)
                                
                                if sheet_cleared:
                                    st.toast(f"✅ {sku_val} permanently deleted.", icon="🗑️")
                                    st.cache_data.clear() 
                                    st.rerun()
                                else:
                                    st.error("⚠️ Failed to delete item from database.")
        else:
            st.info(f"No {filter_cat} items found in the vault yet.")