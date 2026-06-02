from backend.app.rag.retriever import RepoRetriever
from backend.app.core.paths import PROJECT_ROOT


retriever = RepoRetriever()

retriever.build_index(
    str(PROJECT_ROOT)
)

retriever.vector_store.save(
    ".cortex"
)

print("Repository index rebuilt.")