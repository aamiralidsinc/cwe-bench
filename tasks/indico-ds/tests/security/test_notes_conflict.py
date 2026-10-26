"""The payload returned when two editors collide carries the other revision's HTML and
must be inert as well."""

from support import BAD_HTML, assert_html_is_inert


def _event(create_event):
    from indico.modules.events.models.events import EventType
    return create_event(type_=EventType.conference, creator_has_privileges=True)


def test_conflict_payload_delivers_inert_html(create_event, dummy_user, test_client, login):
    event = _event(create_event)
    token = login(dummy_user)
    first = test_client.post(f'/event/{event.id}/api/note', json={'source': BAD_HTML, 'render_mode': 'html'},
                                    headers={'X-CSRF-Token': token})
    assert first.status_code < 500, first.text[:400]

    response = test_client.post(f'/event/{event.id}/api/note',
                                json={'source': 'a later edit', 'render_mode': 'html'},
                                headers={'X-CSRF-Token': token})

    assert response.status_code < 500, response.text[:400]
    assert 'conflict' in response.json, response.text[:400]
    assert_html_is_inert(response.json['conflict']['html'])
