"""
Custom exceptions for the application.
"""


class ContextOverflowError(Exception):
    """
    Exception raised when the input exceeds the maximum context length.
    """

    def __init__(self, estimated_tokens: int, max_context_tokens: int):
        self.estimated_tokens = estimated_tokens
        self.max_context_tokens = max_context_tokens
        self.message = (
            f"The input is too long to be processed "
            f"({estimated_tokens}/{max_context_tokens} tokens)."
        )
        super().__init__(self.message)
