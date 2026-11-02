from tests.conftest import ENHANCE_TEXT, generate_payload


def test_generate_rejects_unknown_category(client, free_user):
    response = client.post("/api/v1/posts/generate", json=generate_payload(category="not-a-type"), headers=free_user)
    assert response.status_code == 422
    body = response.json()["error"]
    assert body["code"] == "invalid_request"
    assert body["details"], "field details should be returned for the form"


def test_generate_rejects_unknown_tone_and_length(client, free_user):
    assert client.post("/api/v1/posts/generate", json=generate_payload(tone="sarcastic"), headers=free_user).status_code == 422
    assert client.post("/api/v1/posts/generate", json=generate_payload(length="epic"), headers=free_user).status_code == 422


def test_generate_rejects_too_short_event(client, free_user):
    response = client.post("/api/v1/posts/generate", json=generate_payload(event="ok"), headers=free_user)
    assert response.status_code == 422


def test_generate_dedupes_keywords_case_insensitively(client, premium_user):
    response = client.post(
        "/api/v1/posts/generate",
        json=generate_payload(keywords=["AI", "ai", "Machine Learning", "machine learning"]),
        headers=premium_user,
    )
    assert response.status_code == 200
    assert response.json()["blueprint"]["keywords"] is not None


def test_generate_rejects_extra_fields(client, free_user):
    response = client.post(
        "/api/v1/posts/generate", json=generate_payload(admin=True), headers=free_user
    )
    assert response.status_code == 422


def test_enhance_rejects_short_text(client, free_user):
    response = client.post("/api/v1/posts/enhance", json={"text": "too short"}, headers=free_user)
    assert response.status_code == 422


def test_enhance_rejects_oversized_text(client, free_user):
    response = client.post("/api/v1/posts/enhance", json={"text": "x" * 5000}, headers=free_user)
    assert response.status_code == 422


def test_post_update_requires_a_field(client, free_user):
    created = client.post("/api/v1/posts/enhance", json={"text": ENHANCE_TEXT}, headers=free_user)
    post_id = created.json()["post_id"]
    response = client.patch(f"/api/v1/posts/{post_id}", json={}, headers=free_user)
    assert response.status_code == 422


def test_unauthenticated_generate_is_rejected(client):
    response = client.post("/api/v1/posts/generate", json=generate_payload())
    assert response.status_code == 401
