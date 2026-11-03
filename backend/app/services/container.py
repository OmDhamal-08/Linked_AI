"""Builds every service once, from configuration.

This is plain manual dependency injection: each class receives what it needs in
its constructor, and this file is the only place that decides which AI provider,
embedding provider and vector store are used. Routes get services through
`get_container()`; tests can swap the whole thing with `reset_container()`.
"""

import logging
from dataclasses import dataclass

from app.ai.factory import build_fallback_provider, build_primary_provider
from app.core.config import Settings, get_settings
from app.core.logging import get_logger, log_event
from app.db.session import dialect_name
from app.embeddings.factory import build_embedding_provider
from app.ingestion.pipeline import IngestionPipeline
from app.prompts.prompt_builder import PromptBuilder
from app.rag.query_builder import QueryAnalyzer
from app.rag.retriever import Retriever
from app.rag.vector_store import VectorStore, build_vector_store
from app.repositories.knowledge_repository import IngestionJobRepository, KnowledgeRepository
from app.repositories.post_repository import PostRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.repositories.usage_repository import UsageRepository
from app.repositories.user_repository import UserRepository
from app.services.ai_service import AIService
from app.services.auth_service import AuthService
from app.services.embedding_service import EmbeddingService
from app.services.feature_access_service import FeatureAccessService
from app.services.generation_service import GenerationService
from app.services.knowledge_service import KnowledgeService
from app.services.post_service import PostService
from app.services.rag_service import RagService
from app.services.subscription_service import SubscriptionService
from app.services.usage_service import UsageService
from app.services.validator_service import PostValidator

logger = get_logger(__name__)


@dataclass
class Container:
    settings: Settings
    ai: AIService
    embeddings: EmbeddingService
    vector_store: VectorStore
    access: FeatureAccessService
    usage: UsageService
    auth: AuthService
    subscriptions: SubscriptionService
    generation: GenerationService
    posts: PostService
    knowledge: KnowledgeService
    users: UserRepository
    usage_repo: UsageRepository
    post_repo: PostRepository


def build_container(settings: Settings | None = None) -> Container:
    s = settings or get_settings()

    # Providers chosen from .env
    ai = AIService(build_primary_provider(s), build_fallback_provider(s))
    embeddings = EmbeddingService(build_embedding_provider(s))
    vector_store = build_vector_store(s.vector_store, dialect_name())

    # Data access
    users = UserRepository()
    usage_repo = UsageRepository()
    post_repo = PostRepository()
    knowledge_repo = KnowledgeRepository()

    # Business logic
    access = FeatureAccessService(s)
    usage = UsageService(usage_repo, access, s)
    rag = RagService(Retriever(vector_store, embeddings, s))
    generation = GenerationService(
        settings=s,
        ai=ai,
        prompts=PromptBuilder(),
        rag=rag,
        query_analyzer=QueryAnalyzer(),
        validator=PostValidator(s),
        access=access,
        usage=usage,
        posts=post_repo,
    )
    pipeline = IngestionPipeline(embeddings=embeddings, repo=knowledge_repo, settings=s)
    knowledge = KnowledgeService(
        pipeline=pipeline, knowledge=knowledge_repo, jobs=IngestionJobRepository(), max_rows=s.ingestion_max_rows
    )

    log_event(
        logger,
        logging.INFO,
        "container_ready",
        ai_provider=ai.primary.name,
        embedding_provider=embeddings.provider_name,
        vector_store=vector_store.name,
    )
    return Container(
        settings=s,
        ai=ai,
        embeddings=embeddings,
        vector_store=vector_store,
        access=access,
        usage=usage,
        auth=AuthService(s, users),
        subscriptions=SubscriptionService(SubscriptionRepository(), s),
        generation=generation,
        posts=PostService(post_repo),
        knowledge=knowledge,
        users=users,
        usage_repo=usage_repo,
        post_repo=post_repo,
    )


_container: Container | None = None


def get_container() -> Container:
    global _container
    if _container is None:
        _container = build_container()
    return _container


def reset_container(container: Container | None = None) -> None:
    """Replace or clear the cached container (used by tests and scripts)."""
    global _container
    _container = container
