import streamlit as st
import pandas as pd
from PIL import Image
import logging
from engines.marketing import generate_instagram_captions

def render_content_generator():
    st.subheader("✨ Caption Generator")
    st.markdown("Instantly generating engaging Instagram copy and hashtags for your latest drops.")

    # --- OPTIMIZATION 1: Context-Aware Pricing (Hardened) ---
    auto_price = ""
    try:
        # Memory Optimization: Fetch ONLY the absolute latest item's pricing directly from SQL
        conn = st.connection("postgresql", type="sql")
        # Since SKUs are generated with a timestamp (e.g., JK-170...), sorting by sku DESC grabs the newest
        latest_item = conn.query("""
            SELECT standard_price, vip_price 
            FROM sourcing_vault 
            ORDER BY sku DESC 
            LIMIT 1;
        """, ttl="10m")
        
        if not latest_item.empty:
            fetched_price = latest_item.iloc[0].get('standard_price', latest_item.iloc[0].get('vip_price', 1500))
            if pd.notna(fetched_price):
                try:
                    # Ensure it is a clean integer string, stripping potential commas
                    auto_price = str(int(float(str(fetched_price).replace(",", ""))))
                except ValueError:
                    auto_price = ""
    except Exception as e:
        logging.warning(f"Silently caught error while fetching auto-price: {e}")

    # 1. The Mode Toggle
    vision_mode = st.toggle("✨ AI Vision Mode (Auto-detect from Images)", value=False)
    
    if vision_mode:
        st.info("Upload or snap a photo of the jewelry. AI will analyze the piece to write the caption.")
        
        col1, col2 = st.columns(2)
        with col1:
            vision_cam = st.camera_input("📸 Camera", key="caption_cam")
        with col2:
            vision_upload = st.file_uploader("📂 Upload", type=["jpg", "png", "jpeg"], key="caption_upload")
        
        active_vision_img = vision_cam or vision_upload
        price_input = st.text_input("Price (₹) *", value=auto_price, placeholder="e.g. 1500")

        # --- OPTIMIZATION 2: Session State Image Caching ---
        if active_vision_img:
            # Create a unique ID for the current image so Streamlit knows if you changed it
            current_img_id = getattr(active_vision_img, 'file_id', 'live_camera_feed')
            
            # Only run the heavy compression if this specific image hasn't been cached yet
            if st.session_state.get('cached_img_id') != current_img_id:
                try:
                    img = Image.open(active_vision_img)
                    img.thumbnail((800, 800)) 
                    # Save the lightweight image into server memory
                    st.session_state['cached_img'] = img
                    st.session_state['cached_img_id'] = current_img_id
                except Exception as e:
                    st.error("⚠️ Failed to process image.")
                    logging.error(f"Image processing error: {e}", exc_info=True)
        
        if st.button("Generate Caption from Image") and active_vision_img and price_input:
            with st.spinner("AI is analyzing the jewelry..."):
                # Directly utilize the pre-compressed cache instead of re-processing
                cached_img = st.session_state.get('cached_img')
                
                if cached_img:
                    captions, error_msg = generate_instagram_captions(price=price_input, image=cached_img)
                    
                    if captions:
                        st.success("Caption Generated!")
                        st.text_area("Copy your caption:", value=captions, height=300)
                    else:
                        st.error(f"⚠️ Could not generate caption. Error details: {error_msg}")
                else:
                    st.error("⚠️ Image cache lost. Please re-upload the image.")
    
    else:
        # 2. The Manual Fallback (Low Network / Text-Only)
        with st.form("text_caption_form", clear_on_submit=False):
            product_name = st.text_input("Product Name *", placeholder="e.g. Mint Green Kundan Set")
            features = st.text_area("Key Features", placeholder="e.g. Gold plated, pearl drops, lightweight...")
            price_input = st.text_input("Price (₹) *", value=auto_price, placeholder="e.g. 1500")
            
            submit_text_caption = st.form_submit_button("Generate Caption from Text")
        
        if submit_text_caption and product_name and price_input:
            with st.spinner("Drafting caption..."):
                captions, error_msg = generate_instagram_captions(
                    price=price_input, 
                    product_name=product_name, 
                    features=features
                )
                
                if captions:
                    st.success("Caption Generated!")
                    st.text_area("Copy your caption:", value=captions, height=300)
                else:
                    st.error(f"⚠️ Could not generate caption. Error details: {error_msg}")