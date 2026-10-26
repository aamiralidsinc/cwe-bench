"""A deployment that requires authentication does not hand accounts to strangers."""

import support


def test_anonymous_caller_cannot_create_an_account():
    with support.make_client() as client:
        email = support.new_email()
        response = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "Password123!"},
        )

        assert support.is_client_error(
            response.status_code
        ), "an anonymous caller created an account: %s %s" % (
            response.status_code,
            response.text[:300],
        )

        logged_in = support.login(client, email)
        assert logged_in.status_code >= 400, (
            "the refused registration still produced a usable account (%s)" % email
        )


def test_no_account_is_created_after_a_refused_registration():
    with support.make_client() as client:
        email = support.new_email()
        first = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "Password123!"},
        )
        second = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "Password123!"},
        )

        assert support.is_client_error(first.status_code)
        assert support.is_client_error(second.status_code)
        assert support.login(client, email).status_code >= 400
