"""The priority-queue chat route selects a model and dispatches it without the
shared request processing that every other chat route runs. A caller-supplied
URL-valued model must still be refused before dispatch."""

import pytest

ATTACK_MODEL = "huggingface/https://example.invalid/v1"


@pytest.mark.parametrize("shape", ["body", "query"])
def test_url_valued_model_on_queue_route_is_refused(client, auth, outbound, shape):
    body = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": "hello"}],
        "priority": 1,
    }
    path = "/queue/chat/completions"
    if shape == "body":
        body["model"] = ATTACK_MODEL
    else:
        path = f"{path}?model={ATTACK_MODEL}"

    with outbound("acompletion") as stub:
        response = client.post(path, headers=auth, json=body)

    assert 400 <= response.status_code < 500, response.text[:300]
    assert not stub.mock.called, "the queued request reached the provider at the caller's destination"
