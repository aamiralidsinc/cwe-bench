"""A link target saved through the event's appearance settings is shown as a link too."""

from support import BAD_URL, assert_clean_refusal, assert_link_is_safe


def _event(create_event):
    from indico.modules.events.models.events import EventType
    return create_event(type_=EventType.conference, creator_has_privileges=True)


def test_event_website_link_with_code_scheme_is_not_saved(create_event, dummy_user, test_client, login, db):
    from indico.modules.events.layout import layout_settings

    event = _event(create_event)
    token = login(dummy_user)
    assert layout_settings.get(event, 'website_url') in (None, '')

    response = test_client.post(
        f'/event/{event.id}/manage/layout/',
        data={'website_url': BAD_URL, 'csrf_token': token},
    )
    db.session.expire_all()

    assert_clean_refusal(response)
    stored = layout_settings.get(event, 'website_url')
    assert stored in (None, ''), f'a code-executing website link was stored: {stored!r}'
    assert_link_is_safe(stored)
