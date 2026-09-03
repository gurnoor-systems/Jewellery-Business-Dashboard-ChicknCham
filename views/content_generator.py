import streamlit as st
from PIL import Image
from data.ingestion import load_sourcing_vault
from engines.marketing import generate_instagram_captions

def render_content_generator():
    st.subheader("✨ Caption Generator")
    st.markdown("Instantly generating engaging Instagram copy and hashtags for your latest drops.")

    # --- OPTIMIZATION 1: Context-Aware Pricing ---
    auto_price = ""
    try:
        vault_df = load_sourcing_vault()
        if not vault_df.empty:
            # Grab the very last item added to the vault
            latest_item = vault_df.iloc[-1]
            # Attempt to pull the Standard price, fallback to VIP, or fallback to an estimate
            fetched_price = latest_item.get('Standard_Price', latest_item.get('VIP_Price', 1500))
            # Ensure it is a clean integer string (e.g., "1500" instead of "1500.0")
            auto_price = str(int(float(fetched_price)))
    except Exception as e:
        pass # If the vault is empty or fails, it remains silent and leaves the box blank

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
                img = Image.open(active_vision_img)
                img.thumbnail((800, 800)) 
                # Save the lightweight image into server memory
                st.session_state['cached_img'] = img
                st.session_state['cached_img_id'] = current_img_id
        
        if st.button("Generate Caption from Image") and active_vision_img and price_input:
            with st.spinner("AI is analyzing the jewelry..."):
                # Compress image in memory
                img = Image.open(active_vision_img)
                img.thumbnail((800, 800)) 
                
                # Clean Engine Call
                captions, error_msg = generate_instagram_captions(price=price_input, image=img)
                
                if captions:
                    st.success("Caption Generated!")
                    st.text_area("Copy your caption:", value=captions, height=300)
                else:
                    st.error(f"⚠️ Could not generate caption. Error details: {error_msg}")
    
    else:
        # 2. The Manual Fallback (Low Network / Text-Only)
        with st.form("text_caption_form", clear_on_submit=False):
            product_name = st.text_input("Product Name *", placeholder="e.g. Mint Green Kundan Set")
            features = st.text_area("Key Features", placeholder="e.g. Gold plated, pearl drops, lightweight...")
            price_input = st.text_input("Price (₹) *", value=auto_price, placeholder="e.g. 1500")
            
            submit_text_caption = st.form_submit_button("Generate Caption from Text")
        
        # We now tie the execution strictly to the form submit button
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