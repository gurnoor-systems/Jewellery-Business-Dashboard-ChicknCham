import google.generativeai as genai
import streamlit as st
import logging

def generate_instagram_captions(price, image=None, product_name=None, features=None):
    """
    Generates Instagram captions using Gemini. 
    If an image is provided, it uses Vision mode. Otherwise, it uses Text-only mode.
    Returns: (generated_text, error_message)
    """
    try:
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
            model = genai.GenerativeModel('gemini-3.1-flash-lite')
            response = model.generate_content([prompt, image])
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
            Output primarily in simple plain English, but include a few Hindi words or phrases to appeal to the local audience in atleast 1 option.
            Also the output is to be highly engaging, considering primary shoppers as women aged 18-55 in India, who are looking for affordable yet stylish artificial jewelry with great lasting quality.
            Customers are majorly from, india but also from Us, Canada, UK, Australia, and Germany. So the captions should be globally appealing but with a strong Indian cultural touch.
            """
            model = genai.GenerativeModel('gemini-3.1-flash-lite')
            response = model.generate_content(prompt)
            return response.text, None

    except Exception as e:
        # Backend logging
        logging.error(f"Marketing API Failure: {e}", exc_info=True)
        # Return the error to be displayed by the UI
        return None, str(e)