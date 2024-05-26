import streamlit as st

# Set page config
st.set_page_config(page_title='Text Trekker', layout='wide', page_icon='🏔️')

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
