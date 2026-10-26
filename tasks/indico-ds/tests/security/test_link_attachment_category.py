"""The same protected value is also entered on a category's own material area."""

from support import BAD_URL, assert_clean_refusal, attachment_link_urls


def test_category_link_attachment_with_code_scheme_is_not_saved(dummy_category, create_user, test_client, login):
    manager = create_user(4242, admin=True)
    token = login(manager)

    response = test_client.post(
        f'/category/{dummy_category.id}/manage/attachments/add/link',
        data={'title': 'Injected', 'link_url': BAD_URL, 'protected': '', 'csrf_token': token},
    )

    assert_clean_refusal(response)
    assert attachment_link_urls() == [], 'a code-executing category material link was stored'
