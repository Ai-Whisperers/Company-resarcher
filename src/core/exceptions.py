class AIError(Exception):
    """Base exception for AI errors."""

    pass


class AIProviderError(AIError):
    """Error related to specific AI provider."""

    def __init__(self, message: str, provider: str, error_code: str = None):
        self.provider = provider
        self.error_code = error_code
        super().__init__(f"[{provider}] {message}")


class AIRateLimitError(AIError):
    """Rate limit exceeded."""

    def __init__(self, provider: str, retry_after: int = None):
        self.provider = provider
        self.retry_after = retry_after
        super().__init__(f"[{provider}] Rate limit exceeded")


class AITimeoutError(AIError):
    """Request timed out."""

    def __init__(self, provider: str, timeout_seconds: int):
        self.provider = provider
        self.timeout_seconds = timeout_seconds
        super().__init__(f"[{provider}] Request timed out after {timeout_seconds}s")


class AIResponseError(AIError):
    """Invalid response from AI."""

    def __init__(self, provider: str, reason: str):
        self.provider = provider
        self.reason = reason
        super().__init__(f"[{provider}] Invalid response: {reason}")
