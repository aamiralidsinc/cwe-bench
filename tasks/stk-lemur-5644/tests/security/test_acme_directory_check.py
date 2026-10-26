import json

import pytest

from lemur.authorities.views import api as authorities_api, AuthorityAcmeDirectory
from support import GOOD_DIRECTORY, make_authority, stored_options


def _post_directory(client, authority, acme_url, token):
    return client.post(
        authorities_api.url_for(AuthorityAcmeDirectory, authority_id=authority.id),
        data=json.dumps({"acmeUrl": acme_url}),
        headers=token,
    )


def test_supplied_directory_is_not_contacted_http(client, session, admin_token, canary):
    authority = make_authority(session, "sec-probe-http", [{"name": "acme_url", "value": GOOD_DIRECTORY}])
    before = stored_options(session, authority.id)

    response = _post_directory(client, authority, canary.http_url, admin_token)

    assert canary.hits == [], "the server contacted the supplied directory address"
    assert response.status_code >= 400
    assert stored_options(session, authority.id) == before


def test_supplied_directory_is_not_contacted_https(client, session, admin_token, canary):
    authority = make_authority(session, "sec-probe-https", [{"name": "acme_url", "value": GOOD_DIRECTORY}])
    before = stored_options(session, authority.id)

    response = _post_directory(client, authority, canary.https_url, admin_token)

    assert canary.hits == [], "the server contacted the supplied directory address"
    assert response.status_code >= 400
    assert stored_options(session, authority.id) == before
