from pathlib import Path

import streamlit as st

# Set page config
st.set_page_config(page_title='Text Trekker', layout='wide', page_icon='🏔️')

style_file = ".streamlit/style.css"
if Path(style_file):
    with open(style_file) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Page
st.title("Text Trekker 🏔")
st.markdown(
    """
    Discover the connections within your documents with **Text Trekker**. This tool utilizes state-of-the-art embedding technology to perform deep similarity searches across multiple PDF files, helping you find relevant information quickly and effectively.
    """
)

with st.sidebar:
    st.markdown(
        """
        ### Coming Soon ...
        """
    )
