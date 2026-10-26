import json

from lemur.authorities import service as authority_service
from lemur.authorities.views import api as authorities_api, Authorities, AuthorityOptions
from support import GOOD_DIRECTORY, make_authority, stored_options


def _put(client, authority, entries, token):
    payload = {
        "owner": authority.owner,
        "description": authority.description or "",
        "active": True,
        "roles": [],
        "options": json.dumps(entries),
    }
    return client.put(
        authorities_api.url_for(Authorities, authority_id=authority.id),
        data=json.dumps(payload),
        headers=token,
    )


def test_allowlisted_directory_can_be_saved(client, session, admin_token):
    authority = make_authority(session, "fn-update-good", [{"name": "email", "value": "a@example.com"}])
    entries = [
        {"name": "acme_url", "value": GOOD_DIRECTORY},
        {"name": "email", "value": "ops@example.com"},
    ]

    response = _put(client, authority, entries, admin_token)

    assert response.status_code == 200
    assert stored_options(session, authority.id) == json.dumps(entries)


def test_options_without_plugin_names_are_saved(client, session, admin_token):
    authority = make_authority(
        session, "fn-update-plain", [{"name": "cab_compliant", "value": True}], plugin="cryptography-issuer"
    )
    entries = [{"updated": "bar"}]

    response = _put(client, authority, entries, admin_token)

    assert response.status_code == 200
    assert stored_options(session, authority.id) == json.dumps(entries)


def test_non_acme_authority_options_are_saved(client, session, admin_token):
    authority = make_authority(
        session,
        "fn-update-crypto",
        [{"name": "cab_compliant", "value": False}],
        plugin="cryptography-issuer",
    )
    entries = [
        {"name": "cab_compliant", "value": True},
        {"name": "validity_years", "value": 1},
    ]

    response = _put(client, authority, entries, admin_token)

    assert response.status_code == 200
    assert stored_options(session, authority.id) == json.dumps(entries)


def test_allowlisted_directory_can_be_saved_by_options_writer(client, session, admin_token):
    authority = make_authority(session, "fn-writer-good", [{"name": "email", "value": "a@example.com"}])
    entries = [
        {"name": "acme_url", "value": GOOD_DIRECTORY},
        {"name": "email", "value": "ops@example.com"},
    ]

    response = client.put(
        authorities_api.url_for(AuthorityOptions, authority_id=authority.id),
        data=json.dumps({"options": json.dumps(entries)}),
        headers=admin_token,
    )

    assert response.status_code == 200
    assert stored_options(session, authority.id) == json.dumps(entries)


def test_internal_option_writes_keep_working(session):
    authority = make_authority(
        session,
        "fn-update-internal",
        [{"name": "acme_url", "value": "https://acme-v01.api.letsencrypt.org/directory"}],
    )
    entries = [{"name": "cab_compliant", "value": False}]

    authority_service.update_options(authority.id, json.dumps(entries))

    assert stored_options(session, authority.id) == json.dumps(entries)
