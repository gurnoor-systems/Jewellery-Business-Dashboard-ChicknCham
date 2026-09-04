from google import genai
import streamlit as st
import logging

def generate_instagram_captions(price, image=None, product_name=None, features=None):
    """
    Generates Instagram captions using Gemini. 
    If an image is provided, it uses Vision mode. Otherwise, it uses Text-only mode.
    Returns: (generated_text, error_message)
    """
    try:
        # Fetch the initialized client from app.py
        client = st.session_state.ai_client
        
        if image:
            # --- 1. VISION MODE LOGIC ---
            prompt = f"""
            You are an expert social media manager for an artificial jewelry brand named 'chik n cham by laddi'.
            With instagram as the primary platform its username is 'chik_n_cham_by_laddi'.
            Analyze this image and write 3 different highly engaging Instagram captions for a new product drop.
            
            The price is ₹{price}. 
            
            Guidelines:
            - Make the captions highly engaging and use relevant emojis.
            - Include a mix of popular and niche hashtags for artificial jewelry in India.
            - Keep the tone elegant but accessible.
            - Include a strong Call to Action (CTA) telling customers to DM to order.
            
            Format the output clearly with headers: Option 1, Option 2, and Option 3.
            Output primarily in simple plain English, but include a few Hindi words or phrases to appeal to the local audience in at least 1 option.
            Also the output is to be highly engaging, considering primary shoppers as women aged 18-55 in India, who are looking for affordable yet stylish artificial jewelry with great lasting quality.
            Customers are majorly from, india but also from Us, Canada, UK, Australia, and Germany. So the captions should be globally appealing but with a strong Indian cultural touch.
            provide the output in a copy-paste ready format, with no extra commentary or explanations.
            worth noting that the captions should be unique and not generic, and should reflect the brand's identity and style.
            """
            
            response = client.models.generate_content(
                model='gemini-3.1-flash-lite',
                contents=[prompt, image]
            )
            return response.text, None
        
        else:
            # --- 2. TEXT-ONLY MODE LOGIC ---
            prompt = f"""
            You are an expert social media manager for an artificial jewelry brand named 'chik n cham by laddi'.
            With instagram as the primary platform its username is 'chik_n_cham_by_laddi'.
            Write 3 different Instagram captions for a new product drop.
        
            Product Name: {product_name}
            Price: ₹{price}
            Key Features: {features}
        
            Guidelines:
            - Make the captions highly engaging and use relevant emojis.
            - Include a mix of popular and niche hashtags for artificial jewelry in India.
            - Keep the tone elegant but accessible.
            - Include a strong Call to Action (CTA) telling customers to DM to order.
        
            Format the output clearly with headers: Option 1, Option 2, and Option 3.
            """
            
            response = client.models.generate_content(
                model='gemini-3.1-flash-lite',
                contents=prompt
            )
            return response.text, None

    except Exception as e:
        logging.error(f"Marketing API Failure: {e}", exc_info=True)
        return None, str(e)

# ------------------------------------------------------------------

def auto_tag_jewelry(image):
    """
    High-speed Vision call to classify jewelry category and generate tags.
    Returns: (category_string, tags_string)
    """
    try:
        client = st.session_state.ai_client
        
        prompt = """
        Analyze this jewelry piece. You must respond in exactly this format with no other text:
        Category: [Category] | Tags: [Tags]
        
        Allowed Categories: Choker Set, Earrings, Bangles, Polki, Kundan, Ring, Other.
        Tags: 3-4 comma-separated visual features (e.g., gold plated, mint green, pearl drops).
        """
        
        response = client.models.generate_content(
            model='gemini-3.1-flash-lite',
            contents=[prompt, image]
        )
        
        text = response.text.strip()
        
        # Default fallbacks
        final_category = "Other"
        final_tags = ""
        
        if "|" in text:
            parts = text.split("|")
            cat_part = parts[0].replace("Category:", "").strip()
            tags_part = parts[1].replace("Tags:", "").strip()
            
            allowed_cats = ["Choker Set", "Earrings", "Bangles", "Polki", "Kundan", "Ring", "Other"]
            for acc in allowed_cats:
                if acc.lower() in cat_part.lower():
                    final_category = acc
                    break
            final_tags = tags_part
            
        return final_category, final_tags
        
    except Exception as e:
        logging.error(f"Auto-Tagging Failure: {e}", exc_info=True)
        return "Other", ""