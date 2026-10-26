import json

import pytest

from lemur.authorities.views import api as authorities_api, AuthorityOptions
from support import ATTACK_HTTP, ATTACK_HTTPS, GOOD_DIRECTORY, make_authority, stored_options


def _put_options(client, authority, entries, token):
    return client.put(
        authorities_api.url_for(AuthorityOptions, authority_id=authority.id),
        data=json.dumps({"options": json.dumps(entries)}),
        headers=token,
    )


@pytest.mark.parametrize("attack", [ATTACK_HTTP, ATTACK_HTTPS])
def test_options_writer_refuses_disallowed_directory(client, session, admin_token, attack):
    authority = make_authority(session, "sec-writer-single", [{"name": "acme_url", "value": GOOD_DIRECTORY}])
    before = stored_options(session, authority.id)

    response = _put_options(client, authority, [{"name": "acme_url", "value": attack}], admin_token)

    assert response.status_code >= 400
    assert stored_options(session, authority.id) == before


def test_options_writer_refuses_disallowed_entry_among_others(client, session, admin_token):
    authority = make_authority(session, "sec-writer-multi", [{"name": "acme_url", "value": GOOD_DIRECTORY}])
    before = stored_options(session, authority.id)

    response = _put_options(
        client,
        authority,
        [
            {"name": "email", "value": "a@example.com"},
            {"name": "acme_url", "value": GOOD_DIRECTORY},
            {"name": "acme_url", "value": ATTACK_HTTP},
        ],
        admin_token,
    )

    assert response.status_code >= 400
    assert stored_options(session, authority.id) == before
