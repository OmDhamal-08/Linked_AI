from tests.conftest import ENHANCE_TEXT


def test_free_enhance_returns_analysis_but_not_enhanced_post(client, seeded, free_user):
    response = client.post("/api/v1/posts/enhance", json={"text": ENHANCE_TEXT}, headers=free_user)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["locked"] is True
    assert body["enhanced_post"] is None
    assert body["analysis"]["topic"]
    assert body["hook_suggestions"]
    assert body["recommended_structure"]
    codes = {s["code"] for s in body["suggestions"]}
    assert "generic_opener" in codes, "the post opens with a generic phrase and should be flagged"
    assert body["score_before"]["overall"] >= 0


def test_premium_enhance_returns_improved_post(client, seeded, premium_user):
    response = client.post(
        "/api/v1/posts/enhance",
        json={"text": ENHANCE_TEXT, "cta": "question", "keywords": ["machine learning"]},
        headers=premium_user,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["locked"] is False
    assert body["enhanced_post"]
    assert "Excited to share" not in body["enhanced_post"]
    assert body["score_after"]["overall"] >= 0
    assert "validation_issues" in body


def test_enhance_keeps_original_facts(client, seeded, premium_user):
    response = client.post("/api/v1/posts/enhance", json={"text": ENHANCE_TEXT}, headers=premium_user)
    enhanced = response.json()["enhanced_post"].lower()
    assert "classifier" in enhanced or "validation" in enhanced or "dataset" in enhanced


def test_analyze_is_free_and_structured(client, free_user):
    response = client.post("/api/v1/posts/analyze", json={"text": ENHANCE_TEXT}, headers=free_user)
    assert response.status_code == 200
    analysis = response.json()["analysis"]
    for key in ("tone", "emotion", "keywords", "hook_type", "hook_strength", "structure", "readability", "cta", "hashtags"):
        assert key in analysis
    assert 0.0 <= analysis["hook_strength"] <= 1.0


def test_advanced_analysis_requires_premium(client, free_user):
    response = client.post("/api/v1/posts/analyze", json={"text": ENHANCE_TEXT, "advanced": True}, headers=free_user)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "subscription_required"


def test_advanced_analysis_for_premium_returns_review(client, premium_user):
    response = client.post("/api/v1/posts/analyze", json={"text": ENHANCE_TEXT, "advanced": True}, headers=premium_user)
    assert response.status_code == 200
    assert isinstance(response.json()["advanced"], dict)


def test_history_list_filters_by_type(client, seeded, premium_user):
    client.post("/api/v1/posts/enhance", json={"text": ENHANCE_TEXT}, headers=premium_user)
    response = client.get("/api/v1/posts?type=enhance", headers=premium_user)
    assert response.status_code == 200
    items = response.json()["items"]
    assert items and all(item["type"] == "enhance" for item in items)


def test_user_cannot_read_another_users_post(client, seeded, premium_user, free_user):
    created = client.post("/api/v1/posts/enhance", json={"text": ENHANCE_TEXT}, headers=premium_user).json()
    response = client.get(f"/api/v1/posts/{created['post_id']}", headers=free_user)
    assert response.status_code == 404


def test_edit_and_delete_post(client, seeded, premium_user):
    created = client.post("/api/v1/posts/enhance", json={"text": ENHANCE_TEXT}, headers=premium_user).json()
    post_id = created["post_id"]
    edited = client.patch(
        f"/api/v1/posts/{post_id}",
        json={"output_text": "Edited text for my post.", "hashtags": ["#AI", "Learning"]},
        headers=premium_user,
    )
    assert edited.status_code == 200
    assert edited.json()["output_text"] == "Edited text for my post."
    assert edited.json()["hashtags"] == ["AI", "Learning"]

    deleted = client.delete(f"/api/v1/posts/{post_id}", headers=premium_user)
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/posts/{post_id}", headers=premium_user).status_code == 404
