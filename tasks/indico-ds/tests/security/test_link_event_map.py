"""A link target saved through the event's location settings is also shown as a link."""

import pytest

from support import BAD_URL, LOCATION_DATA, assert_clean_refusal, assert_link_is_safe


def _event(create_event):
    from indico.modules.events.models.events import EventType
    return create_event(type_=EventType.conference, creator_has_privileges=True)


def test_event_map_link_with_code_scheme_is_not_saved(create_event, dummy_user, test_client, login, db):
    event = _event(create_event)
    token = login(dummy_user)
    assert event.own_map_url in (None, '')

    response = test_client.post(
        f'/event/{event.id}/manage/settings/location',
        data={'own_map_url': BAD_URL, 'location_data': LOCATION_DATA, 'csrf_token': token},
    )
    db.session.expire_all()

    assert_clean_refusal(response)
    assert event.own_map_url in (None, ''), f'a code-executing map link was stored: {event.own_map_url!r}'
    assert_link_is_safe(event.map_url)
