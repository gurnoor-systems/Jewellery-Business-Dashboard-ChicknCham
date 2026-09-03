import time
import uuid
import streamlit as st
import pandas as pd
from PIL import Image

from data.ingestion import load_sourcing_vault
from data.storage import upload_to_cloudinary, delete_from_cloudinary
from data.sourcing import compress_image, save_to_sourcing_vault, delete_from_sourcing_vault, restock_inventory
from engines.marketing import auto_tag_jewelry

def render_catalog():
    st.subheader("Point of Source (POS+)")
    st.caption("Snap a photo. Let the AI do the heavy lifting.")

    # Initialize a dynamic key counter for rapid-fire resets
    if 'vault_form_key' not in st.session_state:
        st.session_state.vault_form_key = 0
    svfk = st.session_state.vault_form_key
    
    # Pre-initialize the form fields in memory so the AI can safely overwrite them
    if f"vault_cat_{svfk}" not in st.session_state:
        st.session_state[f"vault_cat_{svfk}"] = "Choker Set"
    if f"vault_tags_{svfk}" not in st.session_state:
        st.session_state[f"vault_tags_{svfk}"] = ""

    # --- STEP 1: CAPTURE ---
    with st.container(border=True):
        st.markdown("##### 📸 Step 1: Capture Item")
        camera_photo = st.camera_input("Take Photo", key=f"vault_cam_{svfk}")
        uploaded_photo = st.file_uploader("Or upload from gallery", type=["jpg", "png", "jpeg"], key=f"vault_upload_{svfk}")
        active_photo = camera_photo or uploaded_photo

    # --- THE AI OBSERVER ---
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

        # --- STEP 2: REVIEW & SAVE (Form blocks all UI refreshes!) ---
        with st.form(key=f"save_item_form_{svfk}", clear_on_submit=True):
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
            
            # Restoring Custom Pricing safely inside a Form
            with st.expander("⚙️ (click here) to Enter your Custom Pricing", expanded=False):
                st.caption("Leave at ₹0.0 to auto-calculate (1.8x, 1.5x, 1.2x). Enter a value to set a custom price.")
                p_col1, p_col2, p_col3 = st.columns(3)
                custom_std_override = p_col1.number_input("Standard (₹)", min_value=0.0, step=50.0, value=0.0)
                custom_vip_override = p_col2.number_input("VIP (₹)", min_value=0.0, step=50.0, value=0.0)
                custom_clr_override = p_col3.number_input("Clearance (₹)", min_value=0.0, step=50.0, value=0.0)

            generated_sku = f"JK-{int(time.time())}-{uuid.uuid4().hex[:4].upper()}"
    
            save_btn = st.form_submit_button("💾 Save to Vault", type="primary", use_container_width=True)

            if save_btn:
                with st.spinner("Securing to database..."):
                    raw_bytes = active_photo.getvalue()
                    compressed_bytes = compress_image(raw_bytes)
                    cdn_url = upload_to_cloudinary(compressed_bytes, generated_sku)

                    if "🚨" not in cdn_url:
                        combined_tags = f"{category}, {raw_tags}" if raw_tags else category
                        
                        # Backend Math Override Logic
                        final_std = custom_std_override if custom_std_override > 0 else float(sourcing_price * 1.8)
                        final_vip = custom_vip_override if custom_vip_override > 0 else float(sourcing_price * 1.5)
                        final_clr = custom_clr_override if custom_clr_override > 0 else float(sourcing_price * 1.2)

                        is_saved = save_to_sourcing_vault(
                            generated_sku, 
                            sourcing_price, 
                            combined_tags, 
                            cdn_url, 
                            final_std, 
                            final_vip, 
                            final_clr,
                            stock_qty
                        )
                
                        if is_saved:
                            st.session_state.vault_form_key += 1
                            st.toast(f"✅ Saved {generated_sku}! Ready for next item.", icon="🎉")
                            st.balloons() # UX Delight for the client
                            st.cache_data.clear() 
                            st.rerun() 
                        else:
                            st.error("⚠️ Failed to update database.")
                    else:
                        st.error(cdn_url)

    # 3. Recently Cataloged Mini-Gallery
    st.divider()
    st.markdown("##### 🕒 Cataloged Inventory")

    vault_df = load_sourcing_vault()
    if not vault_df.empty:
        # MOBILE UPGRADE: Category & Soft Archival Filters
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
        
        # Apply Pandas filtering logic based on selections
        display_df = vault_df.copy()
        
        # 1. Soft Archival Filter
        display_df['Stock_Quantity'] = pd.to_numeric(display_df.get('Stock_Quantity', 0), errors='coerce').fillna(0)
        
        if hide_sold_out:
            display_df = display_df[display_df['Stock_Quantity'] > 0]

        # 2. Category Filter
        if filter_cat != "All":
            display_df = display_df[display_df['tags'].astype(str).str.contains(filter_cat, case=False, na=False)]

        recent_items = display_df.tail(6).iloc[::-1]  
        
        if not recent_items.empty:
            grid_cols = st.columns(2)
            for idx, (_, item) in enumerate(recent_items.iterrows()):
                with grid_cols[idx % 2]:
                    with st.container(border=True):
                        if 'image_url' in item and str(item['image_url']).strip():
                            st.image(item['image_url'], use_column_width=True)
                        
                        sku_val = item.get('Item_SKU', 'N/A')
                        st.code(sku_val, language=None)
                        
                        # MOBILE UPGRADE: Visual Stock Badges
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

                        # UPGRADE: The Restock Loop
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