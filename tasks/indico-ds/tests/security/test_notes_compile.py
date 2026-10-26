"""Compiling the minutes returns several notes at once; each one must be inert."""

from datetime import timedelta

from support import BAD_HTML, assert_html_is_inert


def _event(create_event):
    from indico.modules.events.models.events import EventType
    return create_event(type_=EventType.conference, creator_has_privileges=True)


def test_compiled_minutes_deliver_inert_html(create_event, dummy_user, create_contribution,
                                             create_timetable_entry, test_client, login):
    from indico.util.date_time import now_utc

    event = _event(create_event)
    token = login(dummy_user)
    contribution = create_contribution(event, 'Contribution', duration=timedelta(minutes=30))
    create_timetable_entry(event, contribution, now_utc())
    saved = test_client.post(
        f'/event/{event.id}/contributions/{contribution.id}/api/note',
        json={'source': BAD_HTML, 'render_mode': 'html'},
        headers={'X-CSRF-Token': token},
    )
    assert saved.status_code < 500, saved.text[:400]

    response = test_client.get(f'/event/{event.id}/api/scheduled-notes')

    assert response.status_code < 500, response.text[:400]
    notes = response.json['notes']
    assert notes, 'the compiled minutes were empty'
    for note in notes:
        assert_html_is_inert(note['html'])
