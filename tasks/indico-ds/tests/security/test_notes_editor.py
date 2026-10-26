"""Minutes HTML handed to the editor must be inert, on the response that saves it and
on the response that reads it back."""

import pytest

from support import BAD_HTML, assert_html_is_inert


def _event(create_event):
    from indico.modules.events.models.events import EventType
    return create_event(type_=EventType.conference, creator_has_privileges=True)


def _save_note(test_client, event, source, token):
    return test_client.post(
        f'/event/{event.id}/api/note',
        json={'source': source, 'render_mode': 'html'},
        headers={'X-CSRF-Token': token},
    )


def test_editor_get_delivers_inert_html(create_event, dummy_user, test_client, login):
    event = _event(create_event)
    token = login(dummy_user)
    saved = _save_note(test_client, event, BAD_HTML, token)
    assert saved.status_code < 500, saved.text[:400]

    response = test_client.get(f'/event/{event.id}/api/note')

    assert response.status_code < 500, response.text[:400]
    assert_html_is_inert(response.json['html'])


def test_editor_save_response_delivers_inert_html(create_event, dummy_user, test_client, login):
    event = _event(create_event)
    token = login(dummy_user)

    response = _save_note(test_client, event, BAD_HTML, token)

    assert response.status_code < 500, response.text[:400]
    assert_html_is_inert(response.json['html'])
