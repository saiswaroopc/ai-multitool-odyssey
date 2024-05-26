import traceback

from .database_manager import DatabaseManager
from .llm_interface import LLMInterface


class DBChatbotApplication:
    """
    Core controller for the AI-powered chat application, managing interactions,
    processing queries, and formatting responses.
    """

    def __init__(self, db_config, api_key):
        """
        Initializes the core components needed for the chatbot.

        :param db_config: dict - Configuration parameters for the database.
        :param api_key: str - OpenAI API key for LLM interactions.
        """
        self.database_manager = DatabaseManager(**db_config)
        self.llm_interface = LLMInterface(api_key)

    def initialize_context(self):
        tables_context = []
        tables = self.database_manager.list_tables()
        for table in tables:
            table_definition = self.database_manager.get_table_definition(table)
            tables_context.append(
                {
                    'table_name': table,
                    'table_columns': table_definition['columns'],
                    'table_constraints': table_definition['constraints'],
                    'table_top_3_rows': self.database_manager.get_top_rows(table, row_count=3)
                }
            )
        context_to_format_1 = """Columns of the table '{table_name}':\n{table_columns}\n\nConstraints of the table '{table_name}':\n{table_constraints}\n\nTop 3 rows from the table '{table_name}':\n{table_top_3_rows}\n\n\n"""
        self.llm_interface.code_reference_context = '\n'.join(map(lambda x: context_to_format_1.format(**x), tables_context))

        # context_to_format_2 = """Columns of the table '{table_name}':\n{table_columns}\n\nConstraints of the table '{table_name}':\n{table_constraints}\n\n\n"""
        # self.llm_interface.code_reference_context = '\n'.join(map(lambda x: context_to_format_2.format(**x), tables_context))

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
            return {'error': str(e), 'is_code_generated': False}

    def get_openai_usage_tokens(self):
        return self.llm_interface.token_usage

    def run_query(self, question):
        """
        Runs a user query, processing it through various components.

        :param question: str - The user's query.
        :return: dict - Processed results and response details.
        """
        try:
            # Generate SQL query from LLM
            code_snippet = self.llm_interface.generate_code(question=question)

            # Execute SQL query
            code_outcome = self._execute_generated_code(snippet=code_snippet)
            if code_outcome.get('error'):
                raise code_outcome['error']

            # Interpret/Summarize Outcome
            summary = self.llm_interface.summarize_results(question=question, results=code_outcome)

            # Followup Question Suggestions
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
