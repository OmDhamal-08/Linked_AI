import re

from tests.conftest import generate_payload


def test_free_user_gets_blueprint_without_full_post(client, seeded, free_user):
    response = client.post("/api/v1/posts/generate", json=generate_payload(), headers=free_user)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["locked"] is True
    assert body["post"] is None
    assert body["upgrade_hint"]
    assert body["blueprint"]["structure"]
    assert len(body["blueprint"]["hook_suggestions"]) >= 1
    assert body["analysis"]["category"] == "Machine Learning"
    assert body["suggestions"], "free users still receive actionable suggestions"


def test_premium_user_gets_full_post_with_score(client, seeded, premium_user):
    response = client.post("/api/v1/posts/generate", json=generate_payload(), headers=premium_user)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["locked"] is False
    assert body["post"]
    assert "machine learning" in body["post"].lower()
    assert len(body["hashtags"]) <= 5
    score = body["score"]
    assert "not a prediction of LinkedIn reach" in score["label"]
    for key in ("relevance", "readability", "hook_strength", "structure", "keyword_alignment", "tone_alignment", "cta_quality", "originality_signals", "overall"):
        assert 0 <= score[key] <= 100


def test_generated_post_never_leaks_internal_terms(client, seeded, premium_user):
    response = client.post("/api/v1/posts/generate", json=generate_payload(), headers=premium_user)
    text = response.json()["post"].lower()
    for term in ("retrieved", "knowledge base", "content intelligence", "embedding", "rag"):
        assert term not in text


def test_generation_does_not_fabricate_numbers(client, seeded, premium_user):
    response = client.post(
        "/api/v1/posts/generate",
        json=generate_payload(event="Shipped a dashboard for my team", context="Used Python and pandas."),
        headers=premium_user,
    )
    body = response.json()
    assert re.search(r"\d+%", body["post"]) is None
    assert not any(ch.isdigit() for ch in body["post"]), "no digits should be invented from nothing"


def test_variations_are_limited_for_premium(client, seeded, premium_user):
    response = client.post("/api/v1/posts/generate", json=generate_payload(variations=3), headers=premium_user)
    body = response.json()
    assert len(body["variations"]) == 3


def test_free_user_variations_are_capped_to_one(client, seeded, free_user):
    response = client.post("/api/v1/posts/generate", json=generate_payload(variations=3), headers=free_user)
    assert response.json()["variations"] == []


def test_generated_post_is_saved_to_history(client, seeded, premium_user):
    created = client.post("/api/v1/posts/generate", json=generate_payload(), headers=premium_user).json()
    fetched = client.get(f"/api/v1/posts/{created['post_id']}", headers=premium_user)
    assert fetched.status_code == 200
    assert fetched.json()["output_text"] == created["post"]
    assert fetched.json()["analysis"] is not None


def test_backend_topic_uses_backend_knowledge(client, seeded, premium_user):
    payload = generate_payload(
        category="technical_insight",
        topic="REST API design",
        event="Designed a versioned REST API with FastAPI and clear error responses",
        field="Backend",
        keywords=["api", "fastapi"],
    )
    response = client.post("/api/v1/posts/generate", json=payload, headers=premium_user)
    assert response.status_code == 200
    assert response.json()["analysis"]["category"] == "Backend Development"


def test_gracefully_rejects_when_ai_fails(client, seeded, premium_user, monkeypatch):
    from app.ai.base import AIRequest, AIResult, AIProvider, ProviderError
    from app.services.container import get_container

    class BrokenProvider(AIProvider):
        name = "broken"
        model = "broken"

        def complete(self, request: AIRequest) -> AIResult:
            raise ProviderError("simulated outage")

    container = get_container()
    monkeypatch.setattr(container.ai, "primary", BrokenProvider())
    monkeypatch.setattr(container.ai, "fallback", None)
    response = client.post("/api/v1/posts/generate", json=generate_payload(), headers=premium_user)
    assert response.status_code == 503
    body = response.json()["error"]
    assert body["code"] == "ai_provider_unavailable"
    assert "Traceback" not in response.text
