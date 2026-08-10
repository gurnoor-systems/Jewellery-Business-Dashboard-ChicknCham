import cloudinary
import cloudinary.uploader
import streamlit as st

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
            public_id=f"chickncham/{sku}",
            resource_type="image"
        )
        
        # 3. Return the ultra-fast CDN URL
        return response.get("secure_url")
        
    except Exception as e:
        return f"🚨 CDN Error: {str(e)}"