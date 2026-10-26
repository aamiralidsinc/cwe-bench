import json
from unittest import mock

from lemur.authorities.views import api as authorities_api, AuthorityAcmeDirectory
from lemur.plugins.lemur_acme.acme_handlers import AcmeHandler
from support import make_authority, stored_options


def _probe(client, authority, token, acme_url=""):
    return client.post(
        authorities_api.url_for(AuthorityAcmeDirectory, authority_id=authority.id),
        data=json.dumps({"acmeUrl": acme_url}),
        headers=token,
    )


def test_stored_directory_is_still_contacted(client, session, admin_token, canary):
    authority = make_authority(
        session,
        "fn-legacy-stored",
        [
            {"name": "acme_url", "value": canary.http_url},
            {"name": "store_account", "value": False},
        ],
    )

    _probe(client, authority, admin_token)

    assert canary.hits, "the stored directory was not contacted"


def test_configured_directory_is_still_contacted(client, session, admin_token, canary, monkeypatch):
    authority = make_authority(
        session,
        "fn-legacy-config",
        [{"name": "store_account", "value": False}],
    )
    monkeypatch.setitem(client.application.config, "ACME_DIRECTORY_URL", canary.http_url)

    _probe(client, authority, admin_token)

    assert canary.hits, "the configured fallback directory was not contacted"


def test_allowed_override_is_still_contacted(client, session, admin_token, canary, monkeypatch):
    authority = make_authority(session, "fn-allowed-override", [{"name": "store_account", "value": False}])
    monkeypatch.setitem(
        client.application.config, "ACME_DIRECTORY_HOST_ALLOWLIST", {"127.0.0.1"}
    )

    _probe(client, authority, admin_token, canary.https_url)

    assert canary.hits, "an allowed directory override was not contacted"


def test_account_write_back_keeps_legacy_directory(session):
    legacy_url = "https://acme-v01.api.letsencrypt.org/directory"
    authority = make_authority(
        session,
        "fn-legacy-writeback",
        [
            {"name": "acme_url", "value": legacy_url},
            {"name": "store_account", "value": True},
        ],
    )

    registration = mock.Mock()
    registration.uri = "https://acme-v01.api.letsencrypt.org/acme/reg/1"
    with mock.patch("lemur.plugins.lemur_acme.acme_handlers.ClientV2") as acme_client, mock.patch(
        "lemur.plugins.lemur_acme.acme_handlers.jose.JWKRSA.fields_to_partial_json"
    ) as partial_json:
        partial_json.return_value = {"n": "PwIOkViO"}
        acme_client.return_value.new_account.return_value = registration

        AcmeHandler().setup_acme_client(authority)

    after = stored_options(session, authority.id)
    assert legacy_url in after
    assert "acme_regr" in after
    assert "acme_private_key" in after
