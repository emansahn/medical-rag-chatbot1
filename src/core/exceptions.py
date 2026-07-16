"""
Application exception hierarchy.

Why this exists:
    Raising specific, typed exceptions (instead of generic `Exception`) lets
    the FastAPI layer translate failures into the right HTTP status code and
    a clean, predictable JSON error body — instead of leaking stack traces
    to the client.

Who owns this:
    Person 3 defines and wires the hierarchy. Person 1 and Person 2 are
    encouraged to raise these (e.g. `RetrievalError`, `DocumentProcessingError`)
    from inside their own modules so errors surface consistently end-to-end.
"""


class AppException(Exception):
    """Base class for all application-specific errors."""

    status_code: int = 500
    default_message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class RAGEngineNotReadyError(AppException):
    """Raised when the RAG pipeline (Person 2's engine) is not yet available."""

    status_code = 503
    default_message = "The RAG engine is not ready yet. It is still using a stub response."


class RetrievalError(AppException):
    """Raised when document retrieval fails (empty index, vector store error...)."""

    status_code = 502
    default_message = "Failed to retrieve relevant documents."


class DocumentProcessingError(AppException):
    """Raised by Person 1's pipeline when a document cannot be parsed/cleaned/chunked."""

    status_code = 422
    default_message = "Failed to process the source document."


class LLMGenerationError(AppException):
    """Raised when the LLM call fails or times out."""

    status_code = 502
    default_message = "Failed to generate a response from the language model."


class InvalidRequestError(AppException):
    """Raised for malformed or invalid client requests that pass schema validation
    but fail business-rule validation (e.g. empty question after trimming)."""

    status_code = 400
    default_message = "Invalid request."
