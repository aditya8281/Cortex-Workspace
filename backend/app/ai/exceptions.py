class ModelNotInstalledError(Exception):
    """
    Raised when the requested Ollama model is not installed locally.
    """
    def __init__(self, model: str, message: str | None = None):
        self.model = model
        self.message = message or f"Model '{model}' is not installed in Ollama. Please download it."
        super().__init__(self.message)
