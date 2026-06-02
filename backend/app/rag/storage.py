from pathlib import Path
import pickle
import faiss


class VectorStorage:
    """
    Handles persistence of FAISS indexes and metadata.
    """

    @staticmethod
    def save(index, metadata, path: str):
        base = Path(path)
        base.mkdir(parents=True, exist_ok=True)

        faiss.write_index(
            index,
            str(base / "index.faiss")
        )

        with open(base / "metadata.pkl", "wb") as f:
            pickle.dump(metadata, f)

    @staticmethod
    def load(path: str):
        base = Path(path)

        index_file = base / "index.faiss"
        metadata_file = base / "metadata.pkl"

        if not index_file.exists() or not metadata_file.exists():
            return None

        index = faiss.read_index(
            str(index_file)
        )

        with open(metadata_file, "rb") as f:
            metadata = pickle.load(f)

        return index, metadata