import streamlit as st
from google import genai
from PIL import Image
import io

def analyze_live_item(image_bytes):
    """
    Uses Gemini Vision to instantly extract search tags from a live photo.
    """
    try:
        # Fetch the initialized client from app.py
        client = st.session_state.ai_client
        
        img = Image.open(io.BytesIO(image_bytes))
        
        prompt = """
        Analyze this artificial jewelry piece. 
        Extract the 3 most prominent features (e.g., color, material, style like 'Kundan', 'Choker', 'Green').
        Return ONLY a comma-separated list of these 3 keywords in lowercase.
        """
        
        response = client.models.generate_content(
            model='gemini-3.1-flash-lite',
            contents=[prompt, img]
        )
        return response.text.strip()
        
    except Exception as e:
        return f"🚨 AI Vision Error: {str(e)}"

def find_vault_match(search_query, vault_df):
    """
    Searches the Sourcing Vault database using the AI-extracted tags.
    """
    if vault_df.empty:
        return None

    clean_query = search_query.replace(',', ' ')
    tags = [tag.strip().lower() for tag in clean_query.split() if tag.strip()]
    
    # Simple scoring: count how many AI tags match the vault tags
    def calculate_score(row_tags):
        row_tags_lower = str(row_tags).lower()
        return sum(1 for tag in tags if tag in row_tags_lower)
        
    vault_df['match_score'] = vault_df['tags'].apply(calculate_score)
    
    # Sort by the highest match score
    best_matches = vault_df[vault_df['match_score'] > 0].sort_values(by='match_score', ascending=False)
    
    if not best_matches.empty:
        return best_matches.iloc[0] # Return the top match
    return None