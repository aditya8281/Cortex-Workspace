import pytest
import numpy as np
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.base import Base
from backend.app.models.hierarchical_memory import HierarchicalNode
from backend.app.rag.hierarchical_store import HierarchicalVectorStore
from backend.app.ai.ingestion.chunker import TextChunker
from backend.app.services.hierarchical_indexing import HierarchicalIndexingService


@pytest.fixture(name="db_session", scope="function")
def fixture_db_session(tmp_path):
    db_file = tmp_path / "test_hierarchical.db"
    db_url = f"sqlite:///{db_file}"

    test_engine = create_engine(db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()


@pytest.fixture(name="clean_hierarchical_store")
def fixture_clean_hierarchical_store(tmp_path):
    from backend.app.services.memory_manager import memory_manager
    original_config_file = memory_manager._config_file
    test_config_file = tmp_path / ".cortex_memory_path"
    memory_manager._config_file = test_config_file

    try:
        original_path = memory_manager.get_memory_path()
    except Exception:
        original_path = Path("~/cortex_memory").expanduser().resolve()

    test_vault_path = tmp_path / "cortex_memory"
    memory_manager._test_override_path = test_vault_path
    memory_manager.ensure_vault_structure()

    store = HierarchicalVectorStore(dim=4)
    yield store

    if test_config_file.exists():
        test_config_file.unlink()
    memory_manager._config_file = original_config_file
    if hasattr(memory_manager, "_test_override_path"):
        delattr(memory_manager, "_test_override_path")


def test_hierarchical_vector_store_idmap2(clean_hierarchical_store):
    store = clean_hierarchical_store
    
    # Add vectors to chunk layer
    vectors = np.array([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0]], dtype="float32")
    ids = np.array([101, 102], dtype="int64")
    store.add_vectors("chunk", vectors, ids)
    
    assert store.indices["chunk"].ntotal == 2
    
    # Search L2 distance
    query = np.array([0.9, 0.1, 0.0, 0.0], dtype="float32")
    results = store.search_vectors("chunk", query, top_k=1)
    
    assert len(results) == 1
    assert results[0]["id"] == 101
    assert results[0]["score"] < 0.1
    
    # Reconstruct
    reconstructed = store.reconstruct("chunk", 102)
    assert np.allclose(reconstructed, [0.0, 1.0, 0.0, 0.0])
    
    # Remove vector
    store.remove_vectors("chunk", np.array([101], dtype="int64"))
    assert store.indices["chunk"].ntotal == 1
    
    # Verify remaining vector is 102
    results = store.search_vectors("chunk", query, top_k=1)
    assert results[0]["id"] == 102


def test_custom_chunkers():
    chunker = TextChunker(max_chunk_size=150, overlap=10)
    
    # 1. Section Chunker (Markdown)
    md_text = "# Header 1\nThis is section one content.\n# Header 2\nThis is section two content."
    md_chunks = chunker.chunk_text(md_text, metadata={"file": "doc.md"})
    
    assert len(md_chunks) == 2
    assert "Header 1" in md_chunks[0]["text"]
    assert "section one" in md_chunks[0]["text"]
    assert "Header 2" in md_chunks[1]["text"]
    assert "section two" in md_chunks[1]["text"]
    
    # 2. Semantic Paragraph Chunker (General text)
    text = "Paragraph one is short.\n\nParagraph two is also short and semantic."
    text_chunks = chunker.chunk_text(text, metadata={"file": "note.txt"})
    
    assert len(text_chunks) == 1
    assert "Paragraph one" in text_chunks[0]["text"]
    assert "Paragraph two" in text_chunks[0]["text"]


@pytest.mark.asyncio
async def test_hierarchical_indexing_service(db_session, tmp_path):
    # Setup test workspace folders
    repo_dir = tmp_path / "my_project"
    repo_dir.mkdir()
    
    folder_dir = repo_dir / "backend"
    folder_dir.mkdir()
    
    file_path = folder_dir / "main.py"
    file_path.write_text("def run_app():\n    print('cortex')\n", encoding="utf-8")
    
    # Instantiate service and mock dependencies
    service = HierarchicalIndexingService(dim=384)
    
    # Mock LLMRouter to generate static summaries
    mock_llm = AsyncMock()
    # First call: file summary, Second call: folder summary, Third call: repo summary
    mock_llm.generate.side_effect = [
        "A python main entrypoint running the cortex service.",
        json.dumps({
            "short_description": "Backend API framework folder.",
            "key_topics": ["fastapi", "routes"],
            "important_files": ["main.py"],
            "structure_summary": "Directory containing API modules."
        }),
        json.dumps({
            "short_description": "Cortex workspace repository.",
            "key_topics": ["ai", "embeddings"],
            "important_files": ["README.md", "backend/main.py"],
            "structure_summary": "Full multi-agent project layout."
        })
    ]
    service.router = mock_llm
    
    # Mock SentenceTransformer embedder
    mock_embedder = MagicMock()
    mock_embedder.encode.side_effect = lambda texts: np.random.rand(len(texts), 384).astype("float32")
    service._embedder = mock_embedder
    
    # Set the PROJECT_ROOT directory for FAISS local cache saving
    service.vector_store.base_dir = tmp_path / ".cortex" / "hierarchical"
    
    # Index the repository
    # This will recursively index the repo, folder, file, and chunk nodes
    repo_node = await service.index_repo(str(repo_dir), db_session)
    
    assert repo_node is not None
    assert repo_node.node_type == "repo"
    assert "Cortex workspace repository" in repo_node.content
    
    # Verify hierarchical relational structures are written correctly in SQLite
    file_node = db_session.query(HierarchicalNode).filter(
        HierarchicalNode.node_type == "file"
    ).first()
    
    assert file_node is not None
    assert file_node.path == str(file_path)
    assert file_node.content == "A python main entrypoint running the cortex service."
    
    # Verify file node parent is folder node
    folder_node = db_session.query(HierarchicalNode).filter(
        HierarchicalNode.id == file_node.parent_id
    ).first()
    
    assert folder_node is not None
    assert folder_node.node_type == "folder"
    assert folder_node.path == str(folder_dir)
    assert "Backend API framework" in folder_node.content
    
    # Verify chunk node parent is file node
    chunk_node = db_session.query(HierarchicalNode).filter(
        HierarchicalNode.parent_id == file_node.id,
        HierarchicalNode.node_type == "chunk"
    ).first()
    
    assert chunk_node is not None
    assert "def run_app():" in chunk_node.content
    
    # Test top-down search
    search_results = await service.search("cortex api entrypoint", db_session, top_k=1)
    
    assert len(search_results) == 1
    assert search_results[0]["file_path"] == str(file_path)
    assert "def run_app()" in search_results[0]["text"]


@pytest.mark.asyncio
async def test_incremental_refresh_updates_parent_summaries(db_session, tmp_path):
    repo_dir = tmp_path / "workspace"
    nested_dir = repo_dir / "backend" / "services"
    nested_dir.mkdir(parents=True)

    file_path = nested_dir / "main.py"
    file_path.write_text("def run_app():\n    return 'version one'\n", encoding="utf-8")

    service = HierarchicalIndexingService(dim=384)

    async def fake_generate(prompt: str) -> str:
        if "Produce a JSON object" in prompt:
            label = "version two" if "version two" in prompt else "version one"
            return json.dumps(
                {
                    "short_description": f"{label} folder summary",
                    "key_topics": ["sync", "memory"],
                    "important_files": ["main.py"],
                    "structure_summary": f"{label} structure",
                }
            )
        label = "version two" if "version two" in prompt else "version one"
        return f"{label} file summary"

    service.router = MagicMock()
    service.router.generate = AsyncMock(side_effect=fake_generate)

    mock_embedder = MagicMock()
    mock_embedder.encode.side_effect = lambda texts: np.ones((len(texts), 384), dtype="float32")
    service._embedder = mock_embedder
    service.vector_store.base_dir = tmp_path / ".cortex" / "hierarchical"

    await service.index_repo(str(repo_dir), db_session)

    backend_folder = db_session.query(HierarchicalNode).filter(
        HierarchicalNode.path == str(repo_dir / "backend"),
        HierarchicalNode.node_type == "folder",
    ).first()
    assert backend_folder is not None
    initial_backend_summary = backend_folder.content

    file_path.write_text("def run_app():\n    return 'version two'\n", encoding="utf-8")
    await service.incremental_update(str(file_path), str(repo_dir), db_session)

    refreshed_backend_folder = db_session.query(HierarchicalNode).filter(
        HierarchicalNode.path == str(repo_dir / "backend"),
        HierarchicalNode.node_type == "folder",
    ).first()
    assert refreshed_backend_folder is not None
    assert refreshed_backend_folder.content != initial_backend_summary
    assert "version two" in refreshed_backend_folder.content
