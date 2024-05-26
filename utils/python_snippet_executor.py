import io
import sys


def execute_code_snippet(code_snippet: str, global_vars: dict = None, local_vars: dict = None) -> str:
    if global_vars is None:
        global_vars = {}
    if local_vars is None:
        local_vars = {}

    # Combine global and local variables
    exec_vars = {**global_vars, **local_vars}

    # Capture the standard output
    old_stdout = sys.stdout
    new_stdout = io.StringIO()
    sys.stdout = new_stdout

    try:

        # Execute the code snippet within the given global_vars dictionary
        exec(code_snippet, exec_vars, exec_vars)

        # Capture the output of the executed code
        output = new_stdout.getvalue()

        # Return the output or a message if there was none
        return output if output else ""

    except Exception as e:
        # Return any error messages that occur during execution
        return f"Error: {e}"

    finally:
        # Restore the standard output
        sys.stdout = old_stdout
