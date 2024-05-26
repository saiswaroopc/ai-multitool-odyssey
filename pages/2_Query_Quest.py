import uuid

import streamlit as st
from projects.query_quest.database_manager import DatabaseManager
from projects.query_quest.llm_interface import LLMInterface
from projects.query_quest.app import DBChatbotApplication

# Set page config
st.set_page_config(page_title='Query Quest', page_icon='💰')
# st.session_state.qq = st.session_state

if not (st.session_state.get('qq_agreed_to_disclaimer') and st.session_state.get('qq_connection_verified') and st.session_state.get('qq_api_key_verified') and st.session_state.get('qq_app_initialized')):
    st.title("Query Quest 💰")
    st.markdown(
        """
        Navigate your databases with ease using **Query Quest**, an intuitive chatbot that answers questions using your database content. This tool simplifies complex database queries, offering precise answers and insights without the need for SQL expertise.
        """
    )

# Disclaimer and advice section
if 'qq_agreed_to_disclaimer' not in st.session_state:
    st.session_state['qq_agreed_to_disclaimer'] = False

if not st.session_state['qq_agreed_to_disclaimer']:
    with st.expander("**User Agreement and Usage Policy**", expanded=True):
        st.write("""
            ### User Agreement and Usage Policy
            Welcome to **Query Quest** AI-powered Database Query Chatbot. Before you proceed, please read and agree to the following terms and conditions:

            #### Data and Security
            - **Data Security**: Users are responsible for the security of their database credentials and the integrity of the data queried using this chatbot.
            - **Read-only Access**: It is advisable to use a read-only database user when data manipulation is not intended to prevent accidental data alterations.

            #### Costs and Charges
            - **API Charges**: Charges may apply for the use of the OpenAI API, and users are responsible for being aware of and managing these costs.

            #### Application Features
            - **Functionality**: This application supports querying databases, generating downloadable sheets, visualizing data, and providing AI-driven question suggestions.
            - **Display Limits**: Only the top 10 results are displayed directly in the response. Users are encouraged to utilize the export feature for larger datasets or the visualization feature for graphical representations of the data.

            #### Usage Guidance
            - **Query Clarity**: Ensure your questions are clear and directly related to the data within your database to receive the most accurate responses.
            - **AI Limitations**: Be aware that AI can make mistakes and the provided answers should be verified for accuracy and relevance.

            #### Disclaimer of Liability
            - **No Liability**: The creators and maintainers of this chatbot will not be liable for any errors, inaccuracies, damages, or data loss resulting from its use. You use this chatbot at your own risk.

            #### Note
            - **Beta Disclaimer**: This version of the chatbot is a beta release. It may have bugs, and you may experience stability issues. 

            #### Acceptance of Terms
            Checking the box below indicates that you have read, understood, and agreed to the terms and conditions outlined above. Non-agreement will restrict your access to this chatbot.
            """)
        agree = st.checkbox("I acknowledge and agree to the terms and conditions")

    if not agree:
        st.warning("You must acknowledge and agree to the terms and conditions to use this app.")
        st.stop()
    else:
        st.session_state['qq_agreed_to_disclaimer'] = True
        st.rerun()
else:
    with st.sidebar:
        if not st.session_state.get('qq_app_initialized'):
            st.success("Policy Acknowledged.", icon='✅')

# Database connection section
if 'qq_connection_verified' not in st.session_state:
    st.session_state['qq_connection_verified'] = False

if not st.session_state['qq_connection_verified']:
    with st.expander("**Database Connection Parameters**", expanded=True):
        db_name = st.text_input('Database Name')
        user = st.text_input('User')
        password = st.text_input('Password', type='password')
        host = st.text_input('Host')
        port = st.text_input('Port', '5432')
        schema = st.text_input('Schema', 'public')

    if host and user and password and db_name and port and schema:
        if st.button("Verify Connection"):
            verified = DatabaseManager(
                db_name=db_name, user=user, password=password, host=host, port=port, schema=schema
            ).verify_connection()
            if verified:
                st.success("Connection verified successfully!")
                st.session_state['db_config'] = {
                    'db_name': db_name,
                    'user': user,
                    'password': password,
                    'host': host,
                    'port': port,
                    'schema': schema
                }
                st.session_state['qq_connection_verified'] = True
                st.rerun()
            else:
                st.error("Failed to verify connection. Please check your credentials.")
                st.stop()
    else:
        st.stop()

else:
    with st.sidebar:
        if not st.session_state.get('qq_app_initialized'):
            st.success(" DB Connection Verified.", icon='✅')

# OpenAI API section
if 'qq_api_key_verified' not in st.session_state:
    st.session_state['qq_api_key_verified'] = False

if not st.session_state['qq_api_key_verified']:
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
                st.session_state['qq_api_key_verified'] = True
                st.rerun()
            else:
                st.error("Failed to verify API key. Please check your key.")
                st.stop()
    else:
        st.stop()

else:
    with st.sidebar:
        if not st.session_state.get('qq_app_initialized'):
            st.success("OpenAI API Key Verified.", icon='✅')

# Initialize App
if 'qq_app_initialized' not in st.session_state:
    st.session_state['qq_app_initialized'] = False

if st.session_state['qq_agreed_to_disclaimer'] and st.session_state['qq_connection_verified'] and st.session_state['qq_api_key_verified'] and st.session_state['qq_api_key_verified']:
    if 'qq_app' not in st.session_state:
        st.success('All checks passed!', icon='✅')
        if st.button("Initialize Chat"):
            app = DBChatbotApplication(
                db_config=st.session_state['db_config'],
                api_key=st.session_state['openai_api_key']
            )
            loading_placeholder = st.empty()
            loading_placeholder.text("Initializing...")

            app.initialize_context()
            st.session_state['qq_app'] = app
            st.session_state['qq_history'] = []

            st.session_state['qq_app_initialized'] = True

            loading_placeholder = st.empty()
            st.rerun()

# Chat Messages and Submission
if st.session_state['qq_app_initialized']:

    # Side Panel
    with st.sidebar:
        st.sidebar.empty()
        st.title("Query Quest 💰")
        st.markdown(
            """
            Navigate your databases with ease using **Query Quest**, an intuitive chatbot that answers questions using your database content. This tool simplifies complex database queries, offering quick answers and insights without the need for SQL expertise.
            """
        )
        st.success('All set!', icon='✅')

        # - Usage tokens
        _token_usage = st.session_state.qq_app.get_openai_usage_tokens()
        with st.sidebar:
            st.code(f'''
            Prompt Tokens: {_token_usage['prompt_tokens']}
            Completion Tokens: {_token_usage['completion_tokens']}
            Total Tokens: {_token_usage['total_tokens']}
            ''')

    # Main Chat Panel
    st.markdown('### Talk to your database! 💬')

    # Chat Message Input
    user_query = st.chat_input(placeholder="What is your query?", key="chat_input")


    # - Process Query
    def _process_query(query):
        _response = st.session_state.qq_app.run_query(query)
        st.session_state.qq_history.append((query, _response))
        return _response


    if 'qq_preloaded_question' in st.session_state:
        response = _process_query(st.session_state['qq_preloaded_question'])
        del st.session_state['qq_preloaded_question']
        # - To display the latest interaction immediately
        # with st.chat_message("user"):
        #     st.markdown(user_query)
        # with st.chat_message("assistant"):
        #     st.markdown(response['result'])
    elif user_query:
        response = _process_query(user_query)
        # - To display the latest interaction immediately
        # with st.chat_message("user"):
        #     st.markdown(user_query)
        # with st.chat_message("assistant"):
        #     st.markdown(response['result'])
    else:
        response = {}

    # Chat History
    if 'qq_history' in st.session_state:
        for question, response in st.session_state['qq_history']:
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
                    st.session_state['qq_preloaded_question'] = question
                    st.rerun()
