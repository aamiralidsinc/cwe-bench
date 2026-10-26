"""Editing minutes stays lossless: the author's raw text comes back unchanged and
ordinary formatting, media and links survive rendering."""

from datetime import timedelta

SAFE_SOURCE = (
    '<p>Minutes <strong>marked</strong></p>'
    "<p><img src='https://example.com/pic.png'></p>"
    "<p><a href='https://example.com/ref'>reference</a></p>"
)


def _event(create_event):
    from indico.modules.events.models.events import EventType
    return create_event(type_=EventType.conference, creator_has_privileges=True)


def test_editor_round_trip_keeps_raw_text_and_formatting(create_event, dummy_user, test_client, login):
    event = _event(create_event)
    token = login(dummy_user)
    saved = test_client.post(f'/event/{event.id}/api/note',
                             json={'source': SAFE_SOURCE, 'render_mode': 'html'},
                             headers={'X-CSRF-Token': token})
    assert saved.status_code < 500, saved.text[:400]

    response = test_client.get(f'/event/{event.id}/api/note')
    data = response.json

    assert data['source'] == SAFE_SOURCE, 'the raw authored text was rewritten'
    assert data['render_mode'] == 'html'
    assert '<strong>marked</strong>' in data['html']
    assert 'pic.png' in data['html']
    assert 'https://example.com/ref' in data['html']


def test_conflict_payload_keeps_raw_text_and_formatting(create_event, dummy_user, test_client, login):
    event = _event(create_event)
    token = login(dummy_user)
    first = test_client.post(f'/event/{event.id}/api/note',
                             json={'source': SAFE_SOURCE, 'render_mode': 'html'},
                             headers={'X-CSRF-Token': token})
    assert first.status_code < 500, first.text[:400]

    response = test_client.post(f'/event/{event.id}/api/note',
                                json={'source': 'a later edit', 'render_mode': 'html'},
                                headers={'X-CSRF-Token': token})

    assert response.status_code < 500, response.text[:400]
    conflict = response.json['conflict']
    assert conflict['source'] == SAFE_SOURCE
    assert '<strong>marked</strong>' in conflict['html']


def test_compiled_minutes_keep_fields_and_formatting(create_event, dummy_user, create_contribution,
                                                     create_timetable_entry, test_client, login):
    from indico.util.date_time import now_utc

    event = _event(create_event)
    token = login(dummy_user)
    contribution = create_contribution(event, 'Contribution', duration=timedelta(minutes=30))
    create_timetable_entry(event, contribution, now_utc())
    saved = test_client.post(
        f'/event/{event.id}/contributions/{contribution.id}/api/note',
        json={'source': SAFE_SOURCE, 'render_mode': 'html'},
        headers={'X-CSRF-Token': token},
    )
    assert saved.status_code < 500, saved.text[:400]

    response = test_client.get(f'/event/{event.id}/api/scheduled-notes')

    notes = response.json['notes']
    assert len(notes) == 1
    note = notes[0]
    assert note['source'] == SAFE_SOURCE
    assert note['object_title'] == 'Contribution'
    assert note['render_mode'] == 'html'
    assert '<strong>marked</strong>' in note['html']


def test_note_export_keeps_fields_and_formatting(create_event, dummy_user, test_client, login):
    event = _event(create_event)
    token = login(dummy_user)
    saved = test_client.post(f'/event/{event.id}/api/note',
                             json={'source': SAFE_SOURCE, 'render_mode': 'html'},
                             headers={'X-CSRF-Token': token})
    assert saved.status_code < 500, saved.text[:400]

    response = test_client.get(f'/export/note/{event.id}.json')
    result = response.json['results']

    assert response.status_code == 200
    assert set(result) == {'html', 'url', 'modified_dt', 'user'}
    assert '<strong>marked</strong>' in result['html']
    assert 'pic.png' in result['html']
