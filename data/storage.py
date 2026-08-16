import cloudinary
import cloudinary.uploader
import streamlit as st
import logging

def upload_to_cloudinary(image_bytes, sku):
    """
    Uploads a compressed image to Cloudinary CDN for instant retrieval.
    """
    try:
        # 1. Authenticate using Streamlit secrets
        cloudinary.config( 
            cloud_name = st.secrets["cloudinary"]["cloud_name"], 
            api_key = st.secrets["cloudinary"]["api_key"], 
            api_secret = st.secrets["cloudinary"]["api_secret"],
            secure = True
        )
        
        # 2. Upload the file directly from memory
        # We assign the SKU as the public_id so it's easy to track
        response = cloudinary.uploader.upload(
            image_bytes, 
            public_id=f"chikncham/{sku}",
            resource_type="image"
        )
        
        # 3. Return the ultra-fast CDN URL
        return response.get("secure_url")

    except Exception as e:
        logging.error(f"Cloudinary Upload Failure: {e}", exc_info=True)
        return f"🚨 CDN Error: {str(e)}"

def delete_from_cloudinary(sku):
    """
    Permanently deletes an image from Cloudinary servers to free up storage limits.
    """
    try:
        # The SKU was used as the public_id during upload
        response = cloudinary.uploader.destroy(sku)
        
        # Cloudinary returns 'ok' if successful or 'not found' if it was already deleted
        if response.get('result') in ['ok', 'not found']:
            return True
        return False
    except Exception as e:
        logging.error(f"Cloudinary Deletion Failure: {e}", exc_info=True)
        return False