import google.generativeai as genai
import streamlit as st

def generate_instagram_captions(product_name, price, features):
    """
    Calls the Gemini API to generate engaging Instagram captions.
    """
    try:
        # Securely load the API key from Streamlit secrets
        genai.configure(api_key=st.secrets["gemini"]["api_key"])
        
        # Use the fast and efficient flash model
        # Using Gemini 3.1 Flash Lite for higher rate limits (500/day) to prevent client errors
        model = genai.GenerativeModel('gemini-3.1-flash-lite')
        prompt = f"""
        You are an expert social media manager for an artificial jewelry brand named 'Chick n Cham by laddi'.
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
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"🚨 Error connecting to AI: {str(e)}"