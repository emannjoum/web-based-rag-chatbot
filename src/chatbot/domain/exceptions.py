class AppError(Exception):
    """Base exception for MedAtlas chatbot errors."""


class SearchError(AppError):
    """Raised when context retrieval from external search providers fails."""


class LLMError(AppError):
    """Raised when an LLM provider call fails."""


class RefinementError(AppError):
    """Raised when query refinement or JSON parsing fails irrecoverably."""


class PersistenceError(AppError):
    """Raised when a database read or write operation fails."""
