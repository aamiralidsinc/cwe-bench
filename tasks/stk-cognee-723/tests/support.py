"""Shared helpers for the hidden suites.

The runner sets the deployment posture in the process environment before these
modules import the application, so every helper below talks to the real HTTP
app built by the product.
"""

import uuid


def make_client():
    from fastapi.testclient import TestClient

    from cognee.api.client import app

    return TestClient(app, raise_server_exceptions=False)


def new_email():
    return "user-%s@example.com" % uuid.uuid4().hex[:12]


def register(client, email=None, password="Password123!"):
    email = email or new_email()
    response = client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )
    return response, email


def login(client, email, password="Password123!"):
    return client.post(
        "/api/v1/auth/login", data={"username": email, "password": password}
    )


def provision_ordinary_user(client, email=None, password="Password123!"):
    """Create an ordinary account the way the deploying application does."""
    import asyncio
    from functools import partial

    from cognee.modules.users.methods import create_user

    email = email or new_email()
    make = partial(create_user, email=email, password=password, is_superuser=False)
    portal = getattr(client, "portal", None)
    if portal is not None:
        # Run in the application's own event loop so the database engine is not
        # used from two loops.
        portal.call(make)
    else:
        asyncio.run(make())
    return email


def bearer(token):
    return {"Authorization": "Bearer %s" % token}


def llm_payload(provider="openai", model="gpt-4o", api_key="sk-test-key"):
    return {"llm": {"provider": provider, "model": model, "api_key": api_key}}


def vector_payload(provider="lancedb", url="local-vector-store", api_key="vdb-test-key"):
    return {
        "vector_db": {"provider": provider, "url": url, "api_key": api_key}
    }


def snapshot():
    """The deployment-global configuration, as the product stores it."""
    from cognee.infrastructure.databases.vector import get_vectordb_config
    from cognee.infrastructure.llm import get_llm_config

    llm = get_llm_config()
    vector = get_vectordb_config()
    return (
        llm.llm_provider,
        llm.llm_model,
        llm.llm_endpoint,
        llm.llm_api_key,
        vector.vector_db_provider,
        vector.vector_db_url,
        vector.vector_db_key,
    )


def stored_llm_key():
    from cognee.infrastructure.llm import get_llm_config

    return get_llm_config().llm_api_key


def stored_vector_key():
    from cognee.infrastructure.databases.vector import get_vectordb_config

    return get_vectordb_config().vector_db_key


def is_client_error(status_code):
    return 400 <= status_code < 500
