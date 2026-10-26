"""A material link target that executes code must not be kept, whether the link is
added or an existing one is edited."""

import pytest

from support import BAD_URL, GOOD_URL, assert_clean_refusal, assert_link_is_safe, attachment_link_urls


def _event_for_links(create_event):
    from indico.modules.events.models.events import EventType
    return create_event(type_=EventType.conference, creator_has_privileges=True)


def test_add_link_attachment_with_code_scheme_is_not_saved(create_event, dummy_user, test_client, login):
    event = _event_for_links(create_event)
    token = login(dummy_user)

    response = test_client.post(
        f'/event/{event.id}/manage/attachments/add/link',
        data={'title': 'Injected', 'link_url': BAD_URL, 'protected': '', 'csrf_token': token},
    )

    assert_clean_refusal(response)
    assert attachment_link_urls() == [], 'a code-executing material link was stored'


def test_edit_link_attachment_to_code_scheme_is_not_saved(create_event, dummy_user, test_client, login, db):
    from indico.modules.attachments.models.attachments import Attachment

    event = _event_for_links(create_event)
    token = login(dummy_user)
    added = test_client.post(
        f'/event/{event.id}/manage/attachments/add/link',
        data={'title': 'Material', 'link_url': GOOD_URL, 'protected': '', 'csrf_token': token},
    )
    assert added.status_code < 400, added.text[:400]
    attachment = Attachment.query.filter_by(link_url=GOOD_URL).one()
    folder_id, attachment_id = attachment.folder_id, attachment.id

    response = test_client.post(
        f'/event/{event.id}/manage/attachments/{folder_id}/{attachment_id}/',
        data={'title': 'Material', 'link_url': BAD_URL, 'protected': '', 'folder': '', 'csrf_token': token},
    )
    db.session.expire_all()

    assert_clean_refusal(response)
    assert attachment.link_url == GOOD_URL, 'editing replaced a safe material link with a code-executing one'
    assert_link_is_safe(attachment.link_url)
