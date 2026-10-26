import json

import pytest

from lemur.authorities.views import api as authorities_api, Authorities
from support import ATTACK_HTTP, ATTACK_HTTPS, ATTACK_SCHEME, GOOD_DIRECTORY, make_authority, stored_options


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


@pytest.mark.parametrize("attack", [ATTACK_HTTP, ATTACK_HTTPS, ATTACK_SCHEME])
def test_update_refuses_disallowed_directory_address(client, session, admin_token, attack):
    authority = make_authority(
        session,
        "sec-update-single",
        [{"name": "acme_url", "value": GOOD_DIRECTORY}, {"name": "email", "value": "a@example.com"}],
    )
    before = stored_options(session, authority.id)

    response = _put(client, authority, [{"name": "acme_url", "value": attack}], admin_token)

    assert response.status_code >= 400
    assert stored_options(session, authority.id) == before


@pytest.mark.parametrize(
    "entries",
    [
        [
            {"name": "acme_url", "value": GOOD_DIRECTORY},
            {"name": "acme_url", "value": ATTACK_HTTP},
        ],
        [
            {"name": "acme_url", "value": ATTACK_HTTP},
            {"name": "acme_url", "value": GOOD_DIRECTORY},
        ],
        [
            {"name": "email", "value": "a@example.com"},
            {"name": "acme_url", "value": ATTACK_HTTPS},
        ],
    ],
)
def test_update_refuses_every_disallowed_entry(client, session, admin_token, entries):
    authority = make_authority(session, "sec-update-multi", [{"name": "acme_url", "value": GOOD_DIRECTORY}])
    before = stored_options(session, authority.id)

    response = _put(client, authority, entries, admin_token)

    assert response.status_code >= 400
    assert stored_options(session, authority.id) == before
