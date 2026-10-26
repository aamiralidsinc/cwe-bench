"""Stored minutes HTML is also handed out through the legacy export interface; that
copy must be inert as well."""

from support import BAD_HTML, assert_html_is_inert


def _event(create_event):
    from indico.modules.events.models.events import EventType
    return create_event(type_=EventType.conference, creator_has_privileges=True)


def test_note_export_delivers_inert_html(create_event, dummy_user, test_client, login):
    event = _event(create_event)
    token = login(dummy_user)
    saved = test_client.post(f'/event/{event.id}/api/note', json={'source': BAD_HTML, 'render_mode': 'html'},
                                    headers={'X-CSRF-Token': token})
    assert saved.status_code < 500, saved.text[:400]

    response = test_client.get(f'/export/note/{event.id}.json')

    assert response.status_code == 200, response.text[:400]
    assert_html_is_inert(response.json['results']['html'])
