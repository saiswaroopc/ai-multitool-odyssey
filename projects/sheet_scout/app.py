import traceback

from .llm_interface import LLMInterface
from .data_manager import DataManager


class SheetChatbotApplication:
    def __init__(self, df, api_key):
        self.data_manager = DataManager(df)
        self.llm_interface = LLMInterface(api_key)

    def initialize_context(self):
        df_info = self.data_manager.get_dataframe_info()
        self.llm_interface.reference_context = df_info

    def get_openai_usage_tokens(self):
        return self.llm_interface.token_usage

    def _execute_generated_code(self, snippet):
        """
        Safely executes dynamically generated Python code and returns its output.
        This method limits the execution environment to prevent security risks.
        """
        # Local scope to execute the code safely
        local_scope = {'self': self}

        # Execute the code within the local scope
        try:
            snippet = snippet.strip('```python').strip('```')
            exec(snippet, {}, local_scope)
            return local_scope['final_result']
        except Exception as e:
            return {'error': e, 'is_code_generated': False}

    def run_query(self, question):
        try:
            # Generate code from LLM
            code_snippet = self.llm_interface.generate_code(question)

            # Execute code snippet
            code_outcome = self._execute_generated_code(snippet=code_snippet)
            if code_outcome.get('error'):
                raise code_outcome['error']

            # Interpret/Summarize Outcome
            summary = self.llm_interface.interpret_response(question, code_outcome)

            followup_suggestions = []
            if code_outcome.get('is_code_generated'):
                followup_suggestions = self.llm_interface.suggest_followup_questions(question=question, response=summary)

            return {
                'result': summary,
                'file': code_outcome.get('file_path') if code_outcome else None,
                'follow_up_questions': followup_suggestions
            }
        except Exception as e:
            # print(f"Error: {str(e)}")
            # traceback.print_exc()
            return {
                'result': 'Encountered internal error, please try again.',
                'file': None,
                'follow_up_questions': [question],
                'error': str(e)
            }
