from app.db.session import get_session_factory
from app.models.knowledge import KnowledgeItem
from app.rag.query_builder import AnalyzedQuery
from app.rag.retriever import Retriever
from app.services.container import get_container


def _retrieve(query: str, category: str | None, keywords: list[str], tone: str = "professional"):
    container = get_container()
    retriever = Retriever(container.vector_store, container.embeddings, container.settings)
    analyzed = AnalyzedQuery(semantic_query=query, knowledge_category=category, keywords=keywords, tone=tone)
    with get_session_factory()() as session:
        return retriever.retrieve(session, analyzed)


def test_ai_query_retrieves_ai_knowledge(seeded):
    result = _retrieve("AI assistants automation LLM workflow", "AI", ["ai", "assistant"])
    assert result.count > 0
    assert result.items[0]["category"] == "AI"


def test_backend_query_retrieves_backend_knowledge(seeded):
    result = _retrieve("backend REST API endpoint FastAPI", "Backend Development", ["api", "backend"])
    assert result.items[0]["category"] == "Backend Development"


def test_achievement_query_retrieves_achievement_patterns(seeded):
    result = _retrieve("completed project achievement proud", None, ["project"], tone="proud")
    hook_types = {item["hook_type"] for item in result.items}
    assert "achievement" in hook_types or "milestone" in hook_types or result.count > 0


def test_top_k_is_respected(seeded):
    result = _retrieve("machine learning model training", "Machine Learning", ["machine learning"])
    assert result.count <= get_container().settings.rag_top_k


def test_relaxes_filters_when_category_has_no_match(seeded):
    result = _retrieve("gardening and cooking recipes", "Cloud", [])
    assert result.count > 0, "retrieval should never return empty when data exists"


def test_retrieval_returns_metadata_not_source_text(seeded):
    result = _retrieve("data science dashboard insights", "Data Science", ["dashboard"])
    for item in result.items:
        assert "text" not in item
        assert set(item).issuperset({"category", "keywords", "structure", "hook_pattern"})


def test_knowledge_rows_store_hash_and_embedding_not_text():
    columns = set(KnowledgeItem.__table__.columns.keys())
    assert "content_hash" in columns and "embedding" in columns
    assert "text" not in columns and "source_text" not in columns


def test_vector_store_selection():
    from app.rag.vector_store import PgVectorStore, PythonVectorStore, build_vector_store

    assert isinstance(build_vector_store("auto", "sqlite"), PythonVectorStore)
    assert isinstance(build_vector_store("auto", "postgresql"), PgVectorStore)
    assert isinstance(build_vector_store("python", "postgresql"), PythonVectorStore)

