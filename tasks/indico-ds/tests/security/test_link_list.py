"""Links entered as a list of items follow the same target rules; every item counts,
including a one-item list and a list where only one item is bad."""

import json

from support import BAD_URL, GOOD_URL, assert_clean_refusal, assert_link_is_safe


def _stored_links(event):
    from indico.modules.events.management.settings import privacy_settings
    return privacy_settings.get(event, 'privacy_policy_urls')


def _event(create_event):
    from indico.modules.events.models.events import EventType
    return create_event(type_=EventType.conference, creator_has_privileges=True)


def test_link_list_single_code_scheme_item_is_not_saved(create_event, dummy_user, test_client, login):
    event = _event(create_event)
    token = login(dummy_user)
    payload = [{'title': '', 'url': BAD_URL}]

    response = test_client.post(
        f'/event/{event.id}/manage/privacy',
        data={'privacy_policy_urls': json.dumps(payload), 'privacy_policy': '', 'csrf_token': token},
    )

    assert_clean_refusal(response)
    assert _stored_links(event) == [], 'a code-executing link list item was stored'


def test_link_list_mixed_items_with_one_code_scheme_is_not_saved(create_event, dummy_user, test_client, login):
    event = _event(create_event)
    token = login(dummy_user)
    payload = [
        {'title': 'Safe', 'url': GOOD_URL},
        {'title': 'Injected', 'url': BAD_URL},
    ]

    response = test_client.post(
        f'/event/{event.id}/manage/privacy',
        data={'privacy_policy_urls': json.dumps(payload), 'privacy_policy': '', 'csrf_token': token},
    )

    assert_clean_refusal(response)
    links = _stored_links(event)
    assert links == [], f'a mixed link list with a code-executing item was stored: {links!r}'
    for item in links:
        assert_link_is_safe(item.get('url'))
