import streamlit as st
from cryptography.fernet import Fernet
import pandas as pd

def get_cipher():
    """Retrieves the master encryption key from Streamlit secrets."""
    key = st.secrets["encryption"]["master_key"].encode()
    return Fernet(key)

def encrypt_pii(text):
    """Scrambles sensitive text before writing to the database."""
    if not text or pd.isna(text):
        return text
    cipher = get_cipher()
    return cipher.encrypt(str(text).encode()).decode()

def decrypt_pii(encrypted_text):
    """Unscrambles sensitive text for the dashboard."""
    if not encrypted_text or pd.isna(encrypted_text):
        return encrypted_text
    try:
        cipher = get_cipher()
        return cipher.decrypt(str(encrypted_text).encode()).decode()
    except Exception:
        return encrypted_text