"""Legitimate routing keeps working: ordinary deployment names, URL-valued
destinations the operator has allowlisted, and plain model calls."""

import litellm
import pytest


def test_ordinary_chat_deployment_path_routes(client, auth, outbound):
    with outbound("acompletion") as stub:
        response = client.post(
            "/openai/deployments/gpt-4o/chat/completions",
            headers=auth,
            json={"messages": [{"role": "user", "content": "hello"}]},
        )
    assert response.status_code == 200, response.text[:300]
    assert stub.mock.called


def test_deployment_name_containing_a_provider_prefix_routes(client, auth, outbound):
    with outbound("acompletion") as stub:
        response = client.post(
            "/openai/deployments/openai/gpt-4o/chat/completions",
            headers=auth,
            json={"messages": [{"role": "user", "content": "hello"}]},
        )
    assert response.status_code == 200, response.text[:300]
    assert stub.mock.called


def test_plain_body_model_routes(client, auth, outbound):
    with outbound("acompletion") as stub:
        response = client.post(
            "/v1/chat/completions",
            headers=auth,
            json={"model": "gpt-4o", "messages": [{"role": "user", "content": "hello"}]},
        )
    assert response.status_code == 200, response.text[:300]
    assert stub.mock.called


def test_ordinary_image_deployment_path_routes(client, auth, outbound):
    with outbound("aimage_generation") as stub:
        response = client.post(
            "/openai/deployments/dall-e-3/images/generations",
            headers=auth,
            json={"prompt": "a harmless picture", "n": 1},
        )
    assert response.status_code == 200, response.text[:300]
    assert stub.mock.called


def test_allowlisted_destination_still_routes_on_a_path_model(client, auth, outbound):
    litellm.provider_url_destination_allowed_hosts = ["example.test"]
    with outbound("acompletion") as stub:
        response = client.post(
            "/openai/deployments/huggingface/https://example.test/v1/chat/completions",
            headers=auth,
            json={"model": "gpt-4o", "messages": [{"role": "user", "content": "hello"}]},
        )
    assert response.status_code == 200, response.text[:300]
    assert stub.mock.called


def test_allowlisted_destination_still_routes_on_the_queue_route(client, auth, outbound):
    litellm.provider_url_destination_allowed_hosts = ["example.test"]
    with outbound("acompletion") as stub:
        response = client.post(
            "/queue/chat/completions",
            headers=auth,
            json={
                "model": "huggingface/https://example.test/v1",
                "messages": [{"role": "user", "content": "hello"}],
                "priority": 1,
            },
        )
    assert response.status_code == 200, response.text[:300]
    assert stub.mock.called


def test_ordinary_queue_model_routes(client, auth, outbound):
    with outbound("acompletion") as stub:
        response = client.post(
            "/queue/chat/completions",
            headers=auth,
            json={
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": "hello"}],
                "priority": 1,
            },
        )
    assert response.status_code == 200, response.text[:300]
    assert stub.mock.called


def test_ordinary_moderation_deployment_path_routes(client, auth, outbound):
    with outbound("amoderation") as stub:
        response = client.post(
            "/openai/deployments/text-moderation-stable/moderations",
            headers=auth,
            json={"input": "hello"},
        )
    assert response.status_code == 200, response.text[:300]
    assert stub.mock.called


def test_non_string_model_value_is_left_to_normal_validation(client, auth):
    # Only string identifiers are inspected; an object-valued model is the
    # request validator's business, not the destination guard's.
    response = client.post(
        "/v1/chat/completions",
        headers=auth,
        json={"model": {"not": "a string"}, "messages": []},
    )
    assert response.status_code != 400 or "URL-valued" not in response.text
