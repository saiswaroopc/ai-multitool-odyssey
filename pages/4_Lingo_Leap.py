from pathlib import Path

import streamlit as st

# Set page config
st.set_page_config(page_title='Lingo Leap', layout='wide', page_icon='🗣️')

style_file = ".streamlit/style.css"
if Path(style_file):
    with open(style_file) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Page
st.title("Lingo Leap 🗣️")
st.markdown(
    """
    Bridge the language gap with **Lingo Leap**. This tool is tuned to provide accurate and swift translations across multiple languages. Whether it's for understanding documents or communicating globally, Lingo Leap connects you to the world.
    """
)

with st.sidebar:
    st.markdown(
        """
        ### Coming Soon ...
        """
    )
