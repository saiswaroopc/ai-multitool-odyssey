import openai


class LLMInterface:
    """
    Interface for OpenAI LLM to generate SQL queries, suggest follow-up questions,
    and generate scripts for data processing.
    """
    def __init__(self, api_key):
        """
        Initialize with the OpenAI API key.
        """
        self.api_key = api_key
        openai.api_key = self.api_key
        self.code_reference_context = None
        self.suggestions_reference_context = None
        self.chat_summary_history = []
        self.token_usage = {
            'completion_tokens': 0,
            'prompt_tokens': 0,
            'total_tokens': 0
        }

    def _update_token_usage(self, usage_data):
        """
        Updates the internal token usage counters based on the usage data from a completion.
        """
        self.token_usage['completion_tokens'] += usage_data.completion_tokens
        self.token_usage['prompt_tokens'] += usage_data.prompt_tokens
        self.token_usage['total_tokens'] += usage_data.total_tokens

    def verify_api_key(self):
        """
        Verifies the OpenAI API key by making a test request.
        Returns True if successful, False otherwise.
        """
        try:
            response = openai.completions.create(
                model="babbage-002",
                prompt='Hi',
                max_tokens=5
            )
            if not response:
                return False
            self._update_token_usage(response.usage)
            return True
        except openai.AuthenticationError:
            return False

    def generate_code(self, question: str) -> str:
        """
        Generates an SQL query based on the provided question and context.

        :param question: str - The user's question.
        :return: str - The generated SQL query
        """
        if not self.code_reference_context:
            raise AttributeError("Reference context was not set.")

        system_prompt = f"""
You are a helpful code generator assistant, 'Assistant 1'.
Generate a Python code snippet that effectively addresses the user's question using the provided PostgreSQL database context.
Assume the database connection is already established and use the function `self.database_manager.execute_query()` for executing SQL queries, which accepts queries in string format and returns results as a list of dictionaries which can further loaded into pandas dataframe.
Ensure to have necessary import statements in the code for necessary packages like pandas, matplotlib, os etc,..

Database context, including columns and constraints, and the top three rows for each table, is detailed in: {self.code_reference_context}.

Adhere to these SQL query guidelines:
- Utilize the SQL LIMIT clause to fetch at most 10 results.
- Select only the necessary columns to answer the query, avoiding the selection of all columns from a table.
- Confirm that only column names listed in the context are queried to prevent errors from non-existent columns.  

If file generation (CSVs, graphs, or charts) is requested, ensure files are saved in the '/tmp' directory.
Ensure the generated code snippet to return 'final_result' variable which is a python dictionary always containing the following:
- 'total_rows': Dynamically calculated count of rows of the result relevant to the query.
- 'top_ten_rows': Dynamically derived from the first ten rows of the result, formatted as strings if necessary.
- 'file_path': Dynamically set to the path of any generated files, if applicable.
- 'summary_message': A message summarizing the outcome, which could be constructed using f-strings.
- 'is_code_generated': A boolean indicating whether SQL query was actually generated. Set to True if SQL code was executed, regardless of the result presence.

Handle different query outcomes as follows:
- For irrelevant queries where no SQL code is executed, set 'total_rows' and 'top_ten_rows' to 0 and [], respectively; 'file_path' to None; 'summary_message' to 'Query not relevant to the database content.'; and 'is_code_generated' to False.
- For queries that execute but yield no results, adjust 'total_rows' to 0, 'top_ten_rows' to [], 'file_path' to None, and 'summary_message' to 'No records found.', with 'is_code_generated' set to True.

Have context to the previous questions and responses from 'Assistant 2' only if the question is continuation to the previous questions.

Ensure to generate the code always, and the generated code contains no narrative text, markdown formatting, or explanations. The code must be executable and comply with these guidelines.

Ensure there has to be 'final_result' (not 'final_resul') dictionary returned at the end irrespective of the the query relevance and that should encapsulate all outputs, clearly demonstrating the outcomes of the executed query.
        """
        dialogues = [
            {"role": "system", "content": system_prompt},
        ]
        user_prompt = f"Question:\n{question}\n"
        messages = dialogues + self.chat_summary_history[-4:] + [{"role": "user", "content": user_prompt}]
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            seed=11,
            temperature=0
        )
        response_content = response.choices[0].message.content.strip()
        self._update_token_usage(response.usage)
        return response_content

    def summarize_results(self, question, results) -> str:
        """
        Summarizes the results obtained by code generation assistant in a concise and readable format.

        :param question: str - User's question.
        :param results: str - The outcome of generated code.
        :return: str - The summarized interpretation of the results.
        """
        system_prompt = """
        You are a helpful assistant, 'Assistant 2'.
        Using the results returned by the previously executed python SQL program, interpret and summarize the outcome in a straightforward and statistical manner. Assume the results are stored in a dictionary with the following keys:
        - 'total_rows': Indicates the total number of rows returned by the query.
        - 'top_ten_rows': Contains the first ten rows of the data returned, if any.
        - 'file_path': The location of any file that was generated during the process, if applicable.
        - 'summary_message': A message provided by the previous assistant, summarizing the outcome of the query.
        - 'is_code_generated': A boolean that confirms whether SQL code was executed.

        Your task is to provide a summary based on the user's question and results obtained.
        
        List out the 'top_ten_rows' value if available.
        
        Do not mention the value of 'file_path'.
        
        Offer a brief insight into the data characteristics, utilizing the 'top_ten_rows' to highlight key data trends or notable entries, if applicable.
        
        Deliver the summary in a non-technical language, avoiding any jargon or complex explanations.

        Ensure the summary is concise, focused on essential statistics, and framed positively to encourage user interaction with the findings.
        
        Directly address greetings, statements or any such expressions with a very short response in 10 words without considering the outcome context.
        """
        dialogues = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f'User Question:\nHi\nOutcome:\n{results}'},
            {'role': 'assistant', 'content': 'Hello! How can I assist you?'},
        ]
        messages = dialogues + [{'role': 'user', 'content': f"""User Question:\n{question}\nOutcome:\n{results}"""}]
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.31,
        )
        response_content = response.choices[0].message.content.strip()
        if results['is_code_generated']:
            self.chat_summary_history.append(
                {"role": "user", "content": f"User Question:\n{question}"}
            )
            self.chat_summary_history.append(
                {"role": "assistant", "content": f"Assistant 2:\n{response_content}"}
            )
        self._update_token_usage(response.usage)
        return response_content

    def suggest_followup_questions(self, question: str, response: str) -> list:
        """
        Suggests a follow-up question based on the current question and results.

        :param question: str - The current question asked by the user.
        :param response: str - The summary response from the previous assistant.
        :return: Optional[str] - The suggested next question or None if no suggestion is possible.
        """
        system_prompt = f"""
        You are a helpful assistant taken user role in generation follow up questions from the user's perspective to the database query assistant.
        Based on the user's initial question and the summarized response provided by the assistant, generate less than four insightful follow-up questions.
        
        Each question must be less that 15 words.      
        The questions may crafted for, deeper understating, exporting data, generating visualization.  
         
        The goal is to facilitate a richer interaction with the data, providing avenues for further exploration and more comprehensive understanding, thereby enhancing the user's engagement and curiosity about their data.
        
        Ensure not to generate any questions in case of irrelevancy, greetings, statements and expressions. or if less confident.
          
        Ensure not to generate anything other than followup questions from user's perspective.
        
        Ensure the followup questions must not be same or similar to the user's question.
        
        Separate each question with '--' ensuring no narrative text and explanations.
        """
        dialogues = [{'role': 'system', 'content': system_prompt}]
        example_dialogues = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f'User Question:\nHi\n'},
            {'role': 'assistant', 'content': 'Assistant 2 response:\nHow can I help you?'},
            {'role': 'assistant', 'content': ''},
            # {'role': 'user', 'content': f'User Question:\nHow many big ants in ants table?\n'},
            # {'role': 'assistant', 'content': 'Assistant 2 response:\nThere are 40 big ants.'},
            # {'role': 'assistant', 'content': 'What are ants other that big ants in ants table?--Can you export the big ants from ants table to csv?'}
        ]
        messages = dialogues + example_dialogues + [
                {'role': 'user', 'content': f"""User Question:\n{question}\n"""},
                {"role": "assistant", "content": f"Assistant 2 response:\n{response}\n"},
            ]

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            n=1
        )
        response_content = response.choices[0].message.content.strip()
        self._update_token_usage(response.usage)

        messages = []
        if '--' in response_content:
            for message in response_content.split('--'):
                if message:
                    messages.append(message)
                else:
                    continue
        return messages
