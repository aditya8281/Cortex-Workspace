class ModelNotInstalledError(Exception):
    """
    Raised when the requested Ollama model is not installed locally.
    """
    def __init__(self, model: str, message: str | None = None):
        self.model = model
        self.message = message or f"Model '{model}' is not installed in Ollama. Please download it."
        super().__init__(self.message)


class ExecutorError(Exception):
    """
    Raised when execution fails inside the graph runner.
    """
    def __init__(self, message: str, execution_id: str | None = None):
        self.message = message
        self.execution_id = execution_id
        super().__init__(self.message)

