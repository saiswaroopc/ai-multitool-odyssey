import uuid
from pathlib import Path

import streamlit as st
import pandas as pd
from projects.sheet_scout.app import SheetChatbotApplication
from projects.sheet_scout.llm_interface import LLMInterface

# Set page config
st.set_page_config(page_title='Sheet Scout', page_icon='📈')
# st.session_state.ss = st.session_state

style_file = ".streamlit/style.css"
if Path(style_file):
    with open(style_file) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Page
if not (st.session_state.get('ss_agreed_to_disclaimer') and st.session_state.get('ss_api_key_verified') and st.session_state.get('ss_app_initialized')):
    st.title("Sheet Scout 📈")
    st.markdown(
        """
        Dive into your CSV data with **Sheet Scout**, an interactive chatbot that answers your queries by analyzing spreadsheet data. Simply upload your CSV file, and ask any question for insights and analysis, making data interpretation straightforward and efficient.
        """
    )

# Disclaimer and advice section
if 'ss_agreed_to_disclaimer' not in st.session_state:
    st.session_state['ss_agreed_to_disclaimer'] = False

if not st.session_state['ss_agreed_to_disclaimer']:
    with st.expander("**User Agreement and Usage Policy**", expanded=True):
        st.write("""
        ### User Agreement and Usage Policy
        Welcome to **Sheet Scout**, the AI-powered CSV Data Analysis Tool. Before you proceed, please read and agree to the following terms and conditions:

        #### Data and Security
        - **Data Security**: Users are responsible for the security of the data they upload and for ensuring that the data does not contain sensitive or personal information unless explicitly permitted for use in this context.

        #### Costs and Charges
        - **API Charges**: Usage of the OpenAI API may incur charges, and users are responsible for being aware of and managing these costs.

        #### Application Features
        - **Functionality**: This application supports uploading CSV files, performing data analysis, generating downloadable sheets, visualizing data, and providing AI-driven question insights and suggestions.
        - **Display Limits**: For larger datasets, only summary statistics or limited entries are displayed directly. Users are encouraged to download comprehensive reports if needed.

        #### Usage Guidance
        - **Query Clarity**: Ensure your questions are clear and directly related to the data within your CSV file to receive the most accurate responses.
        - **AI Limitations**: Be aware that AI can make mistakes and the provided answers should be verified for accuracy and relevance.

        #### Disclaimer of Liability
        - **No Liability**: The creators and maintainers of this tool will not be liable for any errors, inaccuracies, damages, or data loss resulting from its use. You use this tool at your own risk.

        #### Note
        - **Beta Disclaimer**: This version of the tool is a beta release. It may contain bugs, and you may experience stability issues.

        #### Acceptance of Terms
        Checking the box below indicates that you have read, understood, and agreed to the terms and conditions outlined above. Non-agreement will restrict your access to this tool.
        """)
        agree = st.checkbox("I acknowledge and agree to the terms and conditions")

    if not agree:
        st.warning("You must acknowledge and agree to the terms and conditions to use this app.")
        st.stop()
    else:
        st.session_state['ss_agreed_to_disclaimer'] = True
        st.rerun()
else:
    with st.sidebar:
        if not st.session_state.get('ss_app_initialized'):
            st.success("Policy Acknowledged.", icon='✅')

# OpenAI API section
if 'ss_api_key_verified' not in st.session_state:
    st.session_state['ss_api_key_verified'] = False

if not st.session_state['ss_api_key_verified']:
    with st.expander("**OpenAI API Key**", expanded=True):
        openai_api_key = st.text_input('Key', type='password')

    if openai_api_key:
        if st.button("Verify Key"):
            verified = LLMInterface(
                api_key=openai_api_key
            ).verify_api_key()
            if verified:
                st.success("OpenAI API Key verified successfully!")
                st.session_state['openai_api_key'] = openai_api_key
                st.session_state['ss_api_key_verified'] = True
                st.rerun()
            else:
                st.error("Failed to verify API key. Please check your key.")
                st.stop()
    else:
        st.stop()

else:
    with st.sidebar:
        if not st.session_state.get('ss_app_initialized'):
            st.success("OpenAI API Key Verified.", icon='✅')

# Initialize App
if 'ss_app_initialized' not in st.session_state:
    st.session_state['ss_app_initialized'] = False

if st.session_state['ss_agreed_to_disclaimer'] and st.session_state['ss_api_key_verified'] and st.session_state['ss_api_key_verified']:
    if 'ss_app' not in st.session_state:

        # Upload file and Init
        uploaded_file = st.file_uploader("Upload CSV document", type="csv")
        if uploaded_file is not None:
            data = pd.read_csv(uploaded_file)
            st.write('Data Snapshot:')
            st.write(data.head(3))

            if st.button("Initialize Chat"):
                app = SheetChatbotApplication(
                    df=data,
                    api_key=st.session_state['openai_api_key']
                )
                loading_placeholder = st.empty()
                loading_placeholder.text("Initializing...")

                app.initialize_context()
                st.session_state['ss_app'] = app
                st.session_state['ss_history'] = []

                st.session_state['ss_app_initialized'] = True

                loading_placeholder = st.empty()
                st.rerun()

# Chat Messages and Submission
if st.session_state['ss_app_initialized']:

    # Side Panel
    with st.sidebar:
        st.sidebar.empty()
        st.title("Sheet Scout 📈")
        st.markdown(
            """
            Dive into your CSV data with **Sheet Scout**, an interactive chatbot that answers your queries by analyzing spreadsheet data. Simply upload your CSV file, and ask any question for insights and analysis, making data interpretation straightforward and efficient.
            """
        )
        st.success('All set!', icon='✅')

        # - Usage tokens
        _token_usage = st.session_state.ss_app.get_openai_usage_tokens()
        with st.sidebar:
            st.code(f'''
            Prompt Tokens: {_token_usage['prompt_tokens']}
            Completion Tokens: {_token_usage['completion_tokens']}
            Total Tokens: {_token_usage['total_tokens']}
            ''')

    # Main Chat Panel
    st.markdown('### Talk to your document! 💬')

    # Chat Message Input
    user_query = st.chat_input(placeholder="What is your query?", key="chat_input")

    # - Process Query
    def _process_query(query):
        _response = st.session_state.ss_app.run_query(query)
        st.session_state.ss_history.append((query, _response))
        return _response


    if 'ss_preloaded_question' in st.session_state:
        response = _process_query(st.session_state['ss_preloaded_question'])
        del st.session_state['ss_preloaded_question']
    elif user_query:
        response = _process_query(user_query)
    else:
        response = {}

    # Chat History
    if 'ss_history' in st.session_state:
        for question, response in st.session_state['ss_history']:
            # with st.container():
            with st.chat_message("user"):
                st.markdown(question)
            with st.chat_message("assistant"):
                st.markdown(response['result'])
                if response['file']:
                    try:
                        with open(response['file'], 'rb') as f:
                            st.download_button('Download file', f, file_name=response['file'], key=str(uuid.uuid4()))
                    except:
                        st.markdown('Unable to fetch the saved file. Try again!')

    # Suggested follow-up questions (if available)
    if 'response' in locals() and response.get('follow_up_questions', []):
        st.markdown("**Suggested Followup Questions:**")
        cols = st.columns(len(response['follow_up_questions']))
        for col, question in zip(cols, response['follow_up_questions']):
            with col:
                if st.button(question):
                    st.session_state['ss_preloaded_question'] = question
                    st.rerun()
