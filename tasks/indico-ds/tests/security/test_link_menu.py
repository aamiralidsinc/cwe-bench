"""A link placed in the event navigation must obey the same target rules, when it is
created and when an existing entry is edited."""

from support import BAD_URL, GOOD_URL, assert_clean_refusal, assert_link_is_safe, menu_link_urls


def _conference_with_custom_menu(create_event, test_client, token):
    from indico.modules.events.models.events import EventType
    event = create_event(type_=EventType.conference, creator_has_privileges=True)
    enabled = test_client.post(
        f'/event/{event.id}/manage/layout/menu/toggle-customize',
        data={'enabled': '1', 'csrf_token': token},
    )
    assert enabled.status_code < 400, enabled.text[:400]
    return event


def test_add_link_menu_entry_with_code_scheme_is_not_saved(create_event, dummy_user, test_client, login):
    token = login(dummy_user)
    event = _conference_with_custom_menu(create_event, test_client, token)

    response = test_client.post(
        f'/event/{event.id}/manage/layout/menu/add?type=user_link',
        data={'title': 'Injected', 'link_url': BAD_URL, 'is_enabled': 'y', 'csrf_token': token},
    )

    assert_clean_refusal(response)
    assert menu_link_urls(event) == [], 'a code-executing navigation link was stored'


def test_edit_link_menu_entry_to_code_scheme_is_not_saved(create_event, dummy_user, test_client, login, db):
    from indico.modules.events.layout.models.menu import MenuEntry

    token = login(dummy_user)
    event = _conference_with_custom_menu(create_event, test_client, token)
    added = test_client.post(
        f'/event/{event.id}/manage/layout/menu/add?type=user_link',
        data={'title': 'Entry', 'link_url': GOOD_URL, 'is_enabled': 'y', 'csrf_token': token},
    )
    assert added.status_code < 400, added.text[:400]
    entry = MenuEntry.query.filter_by(link_url=GOOD_URL).one()

    response = test_client.post(
        f'/event/{event.id}/manage/layout/menu/{entry.id}/',
        data={'title': 'Entry', 'link_url': BAD_URL, 'is_enabled': 'y', 'csrf_token': token},
    )
    db.session.expire_all()

    assert_clean_refusal(response)
    assert entry.link_url == GOOD_URL, 'editing replaced a safe navigation link with a code-executing one'
    assert_link_is_safe(entry.link_url)
