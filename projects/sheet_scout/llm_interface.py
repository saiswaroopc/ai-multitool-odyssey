from openai import OpenAI, AuthenticationError


class LLMInterface:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)
        self.chat_summary_history = []
        self.reference_context = None
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
            response = self.client.completions.create(
                model="babbage-002",
                prompt='Hi',
                max_tokens=5
            )
            if not response:
                return False
            self._update_token_usage(response.usage)
            return True
        except AuthenticationError:
            return False

    def set_reference_context(self, context):
        self.reference_context = context

    def generate_code(self, question):
        if not self.reference_context:
            raise AttributeError("Dataframe context was not set.")

        system_prompt = f"""
You are 'Assistant 1', responsible for generating Python code snippets based on user queries regarding an uploaded CSV file, preloaded as a pandas DataFrame (`self.data_manager.df`). Information about the dataset is detailed in: {self.reference_context}.

**Code Generation Guidelines:**
- Utilize the preloaded `self.data_manager.df` (not `df`) to perform data fetches and manipulations as specified by the user's query.
- Limit result rows to 5 unless the user requests more.
- Select only the necessary columns to prevent errors from accessing non-existent fields.
- Ensure that visualizations required by the question are generated and stored in the '/tmp' directory, not displayed.
- Include necessary import statements for libraries such as pandas, matplotlib, and os.
- Be extremely creative in handling data when specific datapoints are unavailable; indicate uncertainty by using 'probably' in the 'summary_message'.
- Avoid making assumptions about dynamic data like current date or weather conditions which constantly changes.
- Always generate the code for 'final_result' without any assumptions and prefilling.

**Expected Output:**
Generate a clean, executable Python code snippet that:
- Performs DataFrame operations and manages file generation according to user queries.
- Assigns the output to a dictionary named 'final_result' (not 'final_resul') with the following keys:
  - 'total_rows': Dynamically calculated count of rows of the result relevant to the query.
  - 'top_five_rows': Dynamically derived from the first five rows of the result, formatted as strings if necessary.
  - 'file_path': Dynamically set to the path of the generated files with no assumptions, if applicable.
  - 'summary_message': A message summarizing the outcome, formatted with f-strings.
  - 'is_code_generated': A boolean indicating whether the query resulted in any DataFrame operations.

**Handling Query Outcomes:**
- For irrelevant queries: Set 'total_rows' to zero and 'top_five_rows' to empty list, 'file_path' to None, 'summary_message' to 'Question not relevant to the dataset.' or 'Datapoints not avaiable.', and 'is_code_generated' to False stored in 'final_result' variable.
- For queries without results: In 'final_result' variable, adjust 'total_rows' to zero and 'top_five_rows' to empty list, 'file_path' to None, 'summary_message' to 'No records found.', and 'is_code_generated' to True.
- For visualization or export-related or single-answer queries: In 'final_result' variable, provide 'top_five_rows' as an empty list.

**Best Practices:**
- Ensure the code is concise, direct, and follows Python best practices without external dependencies.
- Keep the code free from narrative text, markdown formatting, or explanations, making it executable immediately.
- Consider continuity with 'Assistant 2' for questions that are follow-ups or related to previous interactions.
- Ensure there has to be 'final_result' (not 'final_resul') dictionary returned at the end and that should encapsulate all outputs, clearly demonstrating the outcomes of the executed query.
"""
        dialogues = [
            {"role": "system", "content": system_prompt},
        ]
        user_prompt = f"Question:\n{question}\n"
        messages = dialogues + self.chat_summary_history[-6:] + [{"role": "user", "content": user_prompt}]
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0,
            seed=11,
        )
        response_content = response.choices[0].message.content.strip()
        self._update_token_usage(response.usage)
        return response_content

    def interpret_response(self, question, results):
        if not self.reference_context:
            raise AttributeError("Dataframe context was not set.")

        system_prompt = f"""
        You are a helpful assistant, 'Assistant 2'. Your role is to interpret and summarize the outcome. 
        
        The outcome of this code is stored in a dictionary with the following keys:
        - 'total_rows': Reflects the total count of rows that were relevant to the user's query.
        - 'top_five_rows': Includes the first five rows from the result set.
        - 'file_path': The location of any file that was generated during the process, if applicable.
        - 'summary_message': Contains a concise message crafted by the previous assistant, detailing the results.
        - 'is_code_generated': Confirms whether any DataFrame operations were executed/generated.
        
        Your summary should:
        - Provide a clear statistical overview based on 'total_rows'.
        - Always list 'top_five_rows' when available and highlight any significant data trends or anomalies found.
        - Ensure not to mention 'file_path' and it's value, instead you can advice to download the file.  
        - Exclude and ensure not to mention technical details and keywords about 'file_path', 'dataframe', 'errors', 'code', 'result' in the response to maintain focus on data insights.
        - Use simple language to make the data understandable to non-technical users, ensuring the summary is concise, informative, statistical, and engaging.
        
        Directly address greetings such as 'Hi', 'Great', 'Thanks' or statements or any such expressions with a very short response in 10 words even when the question is not relevant.
        
        This approach ensures the user can understand and utilize the data insights without needing technical knowledge of the underlying processes.
        """
        dialogues = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f'User Question:\nHi\nOutcome:\n{results}'},
            {'role': 'assistant', 'content': 'Hello! How can I assist you?'},
        ]
        messages = dialogues + [{'role': 'user', 'content': f"""User Question:\n{question}\nOutcome:\n{results}"""}]
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.32,
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
        You are a helpful assistant taken user role in generation follow up questions from the user's perspective to the dataframe query assistant.
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

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            n=1
        )
        response_content = response.choices[0].message.content.strip()
        self._update_token_usage(response.usage)

        messages = []
        if '--' in response_content:
            for message in response_content.split('--'):
                message = message.strip()
                if message:
                    messages.append(message)
                else:
                    continue
        return messages
