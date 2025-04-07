class ContextOverflowError(Exception):
    def __init__(self, num_tokens: int, max_tokens: int):
        self.num_tokens = num_tokens
        self.max_tokens = max_tokens
        self.message = (
            f":warning: The previous message is too long "
            f"({num_tokens}/{max_tokens} prompt tokens)."
        )
        super().__init__(self.message)
