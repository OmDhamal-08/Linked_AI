"""Dependency container: builds every service from configuration.

Routes get services from here, so providers (AI, embeddings, vector store,
payments, auth) can be swapped in one place.
"""

import json
import logging
from dataclasses import dataclass

from app.ai.base import AIRequest
from app.ai.factory import build_fallback_provider, build_primary_provider
from app.core.config import Settings, get_settings
from app.core.logging import get_logger, log_event
from app.db.session import dialect_name
from app.embeddings.factory import build_embedding_provider
from app.ingestion.pipeline import IngestionPipeline, parse_enricher_json
from app.prompts.prompt_builder import PromptBuilder
from app.rag.query_builder import QueryAnalyzer
from app.rag.reranker import NoopReranker
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
from app.services.knowledge_service import KnowledgeService
from app.services.payment_service import MockPaymentProvider, PaymentService
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
    prompts: PromptBuilder
    access: FeatureAccessService
    usage: UsageService
    auth: AuthService
    payments: PaymentService
    subscriptions: SubscriptionService
    posts: PostService
    knowledge: KnowledgeService
    users: UserRepository
    usage_repo: UsageRepository
    post_repo: PostRepository


def _make_enricher(ai: AIService, prompts: PromptBuilder):
    def enrich(text: str) -> dict:
        result = ai.complete(prompts.build_extract(text=text))
        return parse_enricher_json(result.text)

    return enrich


def build_container(settings: Settings | None = None) -> Container:
    s = settings or get_settings()
    ai = AIService(build_primary_provider(s), build_fallback_provider(s))
    embeddings = EmbeddingService(build_embedding_provider(s))
    vector_store = build_vector_store(s.vector_store, dialect_name())
    prompts = PromptBuilder()
    access = FeatureAccessService(s)

    users = UserRepository()
    usage_repo = UsageRepository()
    post_repo = PostRepository()
    sub_repo = SubscriptionRepository()
    knowledge_repo = KnowledgeRepository()
    job_repo = IngestionJobRepository()

    reranker = NoopReranker()
    retriever = Retriever(vector_store, embeddings, s, reranker)
    rag = RagService(retriever)
    usage = UsageService(usage_repo, access, s)
    payments = PaymentService(MockPaymentProvider(), allow_mock=s.allow_mock_payments, is_production=s.is_production)
    posts = PostService(
        settings=s,
        ai=ai,
        prompts=prompts,
        rag=rag,
        query_analyzer=QueryAnalyzer(),
        validator=PostValidator(s),
        access=access,
        usage=usage,
        posts=post_repo,
    )
    pipeline = IngestionPipeline(
        embeddings=embeddings,
        repo=knowledge_repo,
        settings=s,
        enricher=_make_enricher(ai, prompts),
    )
    knowledge = KnowledgeService(pipeline=pipeline, knowledge=knowledge_repo, jobs=job_repo, max_rows=s.ingestion_max_rows)

    log_event(
        logger,
        logging.INFO,
        "container_ready",
        ai_provider=ai.primary.name,
        embedding_provider=embeddings.provider_name,
        vector_store=vector_store.name,
        plan_free_full_post=s.free_full_post_enabled,
    )
    return Container(
        settings=s,
        ai=ai,
        embeddings=embeddings,
        vector_store=vector_store,
        prompts=prompts,
        access=access,
        usage=usage,
        auth=AuthService(s, users),
        payments=payments,
        subscriptions=SubscriptionService(sub_repo, payments),
        posts=posts,
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
