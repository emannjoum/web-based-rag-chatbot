class AltibbiError(Exception):
    """Base exception for Altibbi chatbot errors."""


class SearchError(AltibbiError):
    """Raised when context retrieval from external search providers fails."""


class LLMError(AltibbiError):
    """Raised when an LLM provider call fails."""


class RefinementError(AltibbiError):
    """Raised when query refinement or JSON parsing fails irrecoverably."""


class PersistenceError(AltibbiError):
    """Raised when a database read or write operation fails."""
