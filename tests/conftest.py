import sys
from unittest.mock import MagicMock
import numpy as np


class MockSentenceTransformer:

    def __init__(self, *args, **kwargs):
        pass

    def encode(self, texts, *args, **kwargs):
        return np.random.rand(len(texts), 384).tolist()


# Mock sentence_transformers module at import time to prevent real downloads/loading
mock_module = MagicMock()
mock_module.SentenceTransformer = MockSentenceTransformer
sys.modules["sentence_transformers"] = mock_module
