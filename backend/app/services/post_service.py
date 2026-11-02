"""Post workflows: generate, enhance, analyze, and post history.

Free users get the analysis, recommended keywords, structure, hooks and suggestions.
Full posts and enhanced posts are gated by FeatureAccessService (plan + config).
"""

import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.ai.base import AIResult
from app.core.config import Settings
from app.core.errors import AppError, GenerationFailedError, NotFoundError, SubscriptionRequiredError
from app.core.logging import get_logger, log_event
from app.core.taxonomy import get_taxonomy
from app.models.post import Post, PostAnalysis
from app.models.user import User
from app.nlp.analysis import first_line
from app.prompts.prompt_builder import PromptBuilder
from app.repositories.post_repository import PostRepository
from app.schemas.posts import AnalyzeRequest, EnhanceRequest, GenerateRequest, PostUpdate
from app.services.ai_service import AIService
from app.services.analysis_service import (
    analyze_post,
    build_hook_suggestions,
    build_suggestions,
    missing_elements,
)
from app.services.feature_access_service import ENHANCE, GENERATE, FeatureAccessService
from app.services.scoring_service import score_post, taxonomy_structure_for
from app.services.usage_service import UsageService
from app.services.validator_service import PostValidator
from app.rag.query_builder import QueryAnalyzer
from app.services.rag_service import RagService

logger = get_logger(__name__)
UPGRADE_HINT = "Upgrade to Premium to see the full post and advanced suggestions."


class PostService:
    def __init__(
        self,
        *,
        settings: Settings,
        ai: AIService,
        prompts: PromptBuilder,
        rag: RagService,
        query_analyzer: QueryAnalyzer,
        validator: PostValidator,
        access: FeatureAccessService,
        usage: UsageService,
        posts: PostRepository,
    ) -> None:
        self._s = settings
        self._ai = ai
        self._prompts = prompts
        self._rag = rag
        self._qa = query_analyzer
        self._validator = validator
        self._access = access
        self._usage = usage
        self._posts = posts

    # ------------------------------------------------------------------ generate

    def generate(self, session: Session, user: User, req: GenerateRequest) -> dict[str, Any]:
        self._usage.assert_available(session, user, GENERATE)
        target_words = self._s.length_target_words(req.length)
        analyzed = self._qa.for_generation(req)
        outcome = self._rag.retrieve(session, analyzed)
        intel = outcome.intelligence

        structure = list(intel["recommended_structure"]) if outcome.retrieval.count else taxonomy_structure_for(req.category, req.length)
        hooks = build_hook_suggestions(req.topic, req.event, list(intel["hook_patterns"]))
        hashtags = list(intel["hashtag_concepts"])[: self._s.hashtag_max]
        blueprint = {
            "structure": structure,
            "hook_suggestions": hooks,
            "cta": req.cta,
            "keywords": intel["recommended_keywords"],
            "hashtags": hashtags,
        }
        analysis_preview = {
            "post_type": req.category,
            "topic": req.topic,
            "category": analyzed.knowledge_category,
            "tone": req.tone,
            "emotion": req.emotion,
            "keywords": intel["recommended_keywords"][:6],
            "structure": structure,
            "cta": req.cta,
        }
        blueprint_suggestions = self._blueprint_suggestions(structure, intel["recommended_keywords"], hooks)

        if not self._access.can(user.plan, "generate_full_post"):
            post = self._save_post(
                session,
                user,
                type_=GENERATE,
                input_text=f"{req.event}\n{req.context}".strip(),
                output_text=None,
                req_payload=req.model_dump(),
                category=req.category,
                topic=req.topic,
                tone=req.tone,
                keywords_used=[],
                hashtags=hashtags,
                score=None,
                suggestions=blueprint_suggestions,
                analysis=analysis_preview,
            )
            self._usage.record(session, user, feature=GENERATE, status="success", provider="none")
            return self._response(
                session,
                user,
                post_id=post.id,
                post_text=None,
                variations=[],
                keywords_used=[],
                hashtags=hashtags,
                score=None,
                analysis=analysis_preview,
                suggestions=blueprint_suggestions,
                blueprint=blueprint,
                locked=True,
            )

        facts = " ".join(filter(None, [req.topic, req.field, req.event, req.context, " ".join(req.keywords)]))
        variations: list[str] = []
        tokens_in = tokens_out = 0
        provider = model = None
        try:
            for index in range(min(req.variations, self._access.max_variations(user.plan))):
                hook = hooks[index % len(hooks)] if hooks else req.event
                text, result = self._generate_one(
                    req, intel, structure, hashtags, hook, target_words, index, facts, analyzed.keywords
                )
                variations.append(text)
                tokens_in += result.input_tokens
                tokens_out += result.output_tokens
                provider, model = result.provider, result.model
        except AppError as exc:
            self._usage.record(
                session, user, feature=GENERATE, status="failed", provider=provider, model=model, error_code=exc.code
            )
            raise

        primary = variations[0]
        keywords_used = [k for k in list(req.keywords) + intel["recommended_keywords"] if k.lower() in primary.lower()]
        score = score_post(
            primary,
            topic=req.topic,
            keywords=analyzed.keywords,
            tone=req.tone,
            cta=req.cta,
            target_structure=structure,
            requested_keywords=req.keywords or None,
        )
        analysis = analyze_post(primary)
        suggestions = build_suggestions(
            missing_elements(analysis, primary, intel["recommended_keywords"]),
            missing_keywords=[k for k in intel["recommended_keywords"] if k.lower() not in primary.lower()],
        )
        post = self._save_post(
            session,
            user,
            type_=GENERATE,
            input_text=f"{req.event}\n{req.context}".strip(),
            output_text=primary,
            req_payload=req.model_dump(),
            category=req.category,
            topic=req.topic,
            tone=req.tone,
            keywords_used=keywords_used,
            hashtags=hashtags,
            score=score,
            suggestions=suggestions,
            analysis=analysis,
        )
        self._usage.record(
            session,
            user,
            feature=GENERATE,
            status="success",
            provider=provider,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
        )
        return self._response(
            session,
            user,
            post_id=post.id,
            post_text=primary,
            variations=variations,
            keywords_used=keywords_used,
            hashtags=hashtags,
            score=score,
            analysis=analysis,
            suggestions=suggestions,
            blueprint=blueprint,
            locked=False,
        )

    def _generate_one(
        self,
        req: GenerateRequest,
        intel: dict[str, Any],
        structure: list[str],
        hashtags: list[str],
        hook: str,
        target_words: int,
        index: int,
        facts: str,
        keywords: list[str],
    ) -> tuple[str, AIResult]:
        last_result: AIResult | None = None
        for attempt in range(2):
            prompt = self._prompts.build_generate(
                request=req,
                intelligence=intel,
                blueprint={"structure": structure, "hashtags": hashtags},
                target_words=target_words,
                variant=index + attempt,
                hook=hook,
            )
            result = self._ai.complete(prompt)
            last_result = result
            validation = self._validator.validate(
                result.text, user_facts=facts, target_words=target_words, keywords=keywords, topic=req.topic
            )
            if validation.has_severe:
                log_event(logger, logging.WARNING, "generation_rejected", codes=validation.codes, attempt=attempt)
                continue
            if self._s.post_validation_use_llm:
                validation = self._llm_check(validation, facts)
            return validation.cleaned_text, result
        assert last_result is not None
        raise GenerationFailedError()

    # ------------------------------------------------------------------ enhance

    def enhance(self, session: Session, user: User, req: EnhanceRequest) -> dict[str, Any]:
        self._usage.assert_available(session, user, ENHANCE)
        analysis = analyze_post(req.text)
        target_tone = req.tone or analysis["tone"]
        analyzed = self._qa.for_text(req.text, analysis=analysis, tone_hint=req.tone)
        outcome = self._rag.retrieve(session, analyzed)
        intel = outcome.intelligence

        missing_kw = [k for k in intel["recommended_keywords"] if k.lower() not in req.text.lower()][:5]
        codes = missing_elements(analysis, req.text, intel["recommended_keywords"])
        suggestions = build_suggestions(codes, missing_keywords=missing_kw)
        structure = intel["recommended_structure"] if outcome.retrieval.count else analysis["structure"]
        hooks = build_hook_suggestions(analysis["topic"], first_line(req.text)[:120], list(intel["hook_patterns"]))
        score_before = score_post(
            req.text,
            topic=analysis["topic"],
            keywords=analysis["keywords"],
            tone=target_tone,
            cta=req.cta,
            target_structure=structure,
            requested_keywords=req.keywords or None,
        )
        shared = {
            "analysis": analysis,
            "suggestions": suggestions,
            "missing_keywords": missing_kw,
            "recommended_structure": structure,
            "hook_suggestions": hooks,
            "score_before": score_before,
            "plan": user.plan,
        }

        if not self._access.can(user.plan, "enhance_full_post"):
            post = self._save_post(
                session,
                user,
                type_=ENHANCE,
                input_text=req.text,
                output_text=None,
                req_payload=req.model_dump(),
                category=analysis["post_type"],
                topic=analysis["topic"],
                tone=target_tone,
                keywords_used=[],
                hashtags=analysis["hashtags"],
                score=score_before,
                suggestions=suggestions,
                analysis=analysis,
            )
            self._usage.record(session, user, feature=ENHANCE, status="success", provider="none")
            return {**shared, "post_id": post.id, "enhanced_post": None, "score_after": None, "locked": True,
                    "upgrade_hint": UPGRADE_HINT, "usage": self._usage.summary(session, user)}

        tokens_in = tokens_out = 0
        provider = model = None
        try:
            prompt = self._prompts.build_enhance(
                original_text=req.text,
                tone=target_tone,
                cta=req.cta,
                keywords=req.keywords,
                analysis=analysis,
                intelligence=intel,
                hook=hooks[0] if hooks else "",
                weaknesses=[s["message"] for s in suggestions],
                missing_keywords=missing_kw,
            )
            result = self._ai.complete(prompt)
            provider, model = result.provider, result.model
            tokens_in, tokens_out = result.input_tokens, result.output_tokens
            validation = self._validator.validate(
                result.text,
                user_facts=req.text,
                target_words=max(40, analysis["length_words"]),
                keywords=req.keywords,
                topic=analysis["topic"],
            )
            if validation.has_severe:
                raise GenerationFailedError()
            enhanced = validation.cleaned_text
        except AppError as exc:
            self._usage.record(session, user, feature=ENHANCE, status="failed", provider=provider, model=model, error_code=exc.code)
            raise

        score_after = score_post(
            enhanced,
            topic=analysis["topic"],
            keywords=analysis["keywords"],
            tone=target_tone,
            cta=req.cta,
            target_structure=structure,
            requested_keywords=req.keywords or None,
        )
        new_analysis = analyze_post(enhanced)
        post = self._save_post(
            session,
            user,
            type_=ENHANCE,
            input_text=req.text,
            output_text=enhanced,
            req_payload=req.model_dump(),
            category=analysis["post_type"],
            topic=analysis["topic"],
            tone=target_tone,
            keywords_used=[k for k in req.keywords if k.lower() in enhanced.lower()],
            hashtags=new_analysis["hashtags"],
            score=score_after,
            suggestions=suggestions,
            analysis=new_analysis,
        )
        self._usage.record(
            session, user, feature=ENHANCE, status="success", provider=provider, model=model,
            tokens_in=tokens_in, tokens_out=tokens_out,
        )
        return {
            **shared,
            "post_id": post.id,
            "enhanced_post": enhanced,
            "score_after": score_after,
            "locked": False,
            "upgrade_hint": None,
            "validation_issues": validation.codes,
            "usage": self._usage.summary(session, user),
        }

    # ------------------------------------------------------------------ analyze

    def analyze(self, session: Session, user: User, req: AnalyzeRequest) -> dict[str, Any]:
        analysis = analyze_post(req.text)
        codes = missing_elements(analysis, req.text, analysis["keywords"][:3])
        suggestions = build_suggestions(codes, missing_keywords=analysis["keywords"][:3])
        score = score_post(
            req.text,
            topic=analysis["topic"],
            keywords=analysis["keywords"],
            tone=analysis["tone"],
            cta=analysis["cta"] if analysis["cta"] != "none" else "question",
            target_structure=analysis["structure"],
        )
        advanced = None
        if req.advanced:
            if not self._access.can(user.plan, "advanced_analysis"):
                raise SubscriptionRequiredError()
            result = self._ai.complete(self._prompts.build_analyze(original_text=req.text, analysis=analysis))
            advanced = self._parse_json(result.text)
            self._usage.record(session, user, feature="analyze", status="success", provider=result.provider,
                               model=result.model, tokens_in=result.input_tokens, tokens_out=result.output_tokens)
        return {"analysis": analysis, "suggestions": suggestions, "score": score, "advanced": advanced, "plan": user.plan}

    # ------------------------------------------------------------------ history

    def list_posts(self, session: Session, user: User, *, limit: int, offset: int, post_type: str | None, category: str | None) -> dict[str, Any]:
        rows, total = self._posts.list_for_user(
            session, user.id, limit=limit, offset=offset, post_type=post_type, category=category
        )
        return {"items": [self.serialize(p) for p in rows], "total": total, "limit": limit, "offset": offset}

    def get_post(self, session: Session, user: User, post_id: str) -> dict[str, Any]:
        post = self._posts.get_for_user(session, user.id, post_id)
        if not post:
            raise NotFoundError()
        return self.serialize(post)

    def update_post(self, session: Session, user: User, post_id: str, req: PostUpdate) -> dict[str, Any]:
        post = self._posts.get_for_user(session, user.id, post_id)
        if not post:
            raise NotFoundError()
        changes: dict[str, Any] = {}
        if req.output_text is not None:
            changes["output_text"] = req.output_text.strip()
        if req.hashtags is not None:
            changes["hashtags"] = req.hashtags
        post = self._posts.update(session, post, changes)
        return self.serialize(post)

    def delete_post(self, session: Session, user: User, post_id: str) -> None:
        post = self._posts.get_for_user(session, user.id, post_id)
        if not post:
            raise NotFoundError()
        self._posts.delete(session, post)

    def serialize(self, post: Post) -> dict[str, Any]:
        analysis = post.analysis
        return {
            "id": post.id,
            "type": post.type,
            "input_text": post.input_text,
            "output_text": post.output_text,
            "category": post.category,
            "topic": post.topic,
            "tone": post.tone,
            "keywords_used": post.keywords_used or [],
            "hashtags": post.hashtags or [],
            "score": post.score,
            "suggestions": post.suggestions or [],
            "analysis": None if analysis is None else {
                "emotion": analysis.emotion,
                "hook_type": analysis.hook_type,
                "structure": analysis.structure,
                "readability_score": analysis.readability_score,
                "hook_score": analysis.hook_score,
                "keyword_score": analysis.keyword_score,
                "overall_score": analysis.overall_score,
            },
            "created_at": post.created_at.isoformat(),
            "updated_at": post.updated_at.isoformat(),
        }

    # ------------------------------------------------------------------ helpers

    def _save_post(
        self,
        session: Session,
        user: User,
        *,
        type_: str,
        input_text: str,
        output_text: str | None,
        req_payload: dict[str, Any],
        category: str | None,
        topic: str | None,
        tone: str | None,
        keywords_used: list[str],
        hashtags: list[str],
        score: dict[str, Any] | None,
        suggestions: list[dict[str, Any]],
        analysis: dict[str, Any],
    ) -> Post:
        post = Post(
            user_id=user.id,
            type=type_,
            input_text=input_text,
            output_text=output_text,
            category=category,
            topic=topic,
            tone=tone,
            input_payload=req_payload,
            keywords_used=keywords_used,
            hashtags=hashtags,
            score=score,
            suggestions=suggestions,
        )
        analysis_row = PostAnalysis(
            category=analysis.get("category") or analysis.get("knowledge_category") or category,
            topic=analysis.get("topic"),
            tone=analysis.get("tone"),
            emotion=analysis.get("emotion"),
            keywords=list(analysis.get("keywords", [])),
            hook_type=analysis.get("hook_type"),
            structure=list(analysis.get("structure", [])),
            readability_score=float(analysis.get("readability", 0.0)),
            hook_score=float(analysis.get("hook_strength", 0.0)) * 100,
            keyword_score=float((score or {}).get("keyword_alignment", 0.0)),
            overall_score=float((score or {}).get("overall", 0.0)),
        )
        return self._posts.create(session, post, analysis_row)

    def _response(
        self,
        session: Session,
        user: User,
        *,
        post_id: str,
        post_text: str | None,
        variations: list[str],
        keywords_used: list[str],
        hashtags: list[str],
        score: dict[str, Any] | None,
        analysis: dict[str, Any],
        suggestions: list[dict[str, Any]],
        blueprint: dict[str, Any],
        locked: bool,
    ) -> dict[str, Any]:
        return {
            "post_id": post_id,
            "post": post_text,
            "variations": variations,
            "keywords_used": keywords_used,
            "hashtags": hashtags,
            "score": score,
            "analysis": analysis,
            "suggestions": suggestions,
            "blueprint": blueprint,
            "locked": locked,
            "plan": user.plan,
            "upgrade_hint": UPGRADE_HINT if locked else None,
            "usage": self._usage.summary(session, user),
        }

    @staticmethod
    def _blueprint_suggestions(structure: list[str], keywords: list[str], hooks: list[str]) -> list[dict[str, str]]:
        messages = get_taxonomy()["suggestion_messages"]
        items = [
            {"code": "structure", "message": "Follow this flow: " + " → ".join(structure)},
        ]
        if hooks:
            items.append({"code": "hook", "message": "Try a hook like: " + hooks[0]})
        if keywords:
            items.append({"code": "keywords", "message": messages["missing_keywords"].format(keywords=", ".join(keywords[:4]))})
        return items

    def _llm_check(self, validation, facts: str):
        result = self._ai.complete(self._prompts.build_validate(post=validation.cleaned_text, user_facts=facts))
        verdict = self._parse_json(result.text) or {}
        if verdict.get("valid") is False:
            from app.services.validator_service import ValidationIssue

            for issue in verdict.get("issues", [])[:3]:
                validation.issues.append(ValidationIssue("warning", "llm_review", str(issue)[:200]))
        return validation

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any] | None:
        try:
            value = json.loads(text)
            return value if isinstance(value, dict) else None
        except (json.JSONDecodeError, TypeError):
            start, end = text.find("{"), text.rfind("}")
            if start != -1 and end > start:
                try:
                    return json.loads(text[start : end + 1])
                except json.JSONDecodeError:
                    return None
            return None
