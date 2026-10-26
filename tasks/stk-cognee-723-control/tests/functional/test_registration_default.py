"""With the default posture, self-registration still onboards ordinary users."""

import support


def test_registration_still_works_when_the_deployment_allows_it():
    with support.make_client() as client:
        response, email = support.register(client)
        assert response.status_code < 400, response.text[:300]
        assert response.json().get("email") == email

        logged_in = support.login(client, email)
        assert logged_in.status_code < 400, logged_in.text[:300]
        assert logged_in.json().get("access_token")
