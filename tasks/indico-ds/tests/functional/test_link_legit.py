"""Ordinary web links keep working exactly as before, in every entry surface."""

import json

from support import GOOD_URL, GOOD_URL2, LOCATION_DATA


def _event(create_event):
    from indico.modules.events.models.events import EventType
    return create_event(type_=EventType.conference, creator_has_privileges=True)


def test_material_link_add_and_edit_keep_working(create_event, dummy_user, test_client, login, db):
    from indico.modules.attachments.models.attachments import Attachment

    event = _event(create_event)
    token = login(dummy_user)
    added = test_client.post(
        f'/event/{event.id}/manage/attachments/add/link',
        data={'title': 'Material', 'link_url': GOOD_URL, 'protected': '', 'csrf_token': token},
    )
    assert added.status_code < 400, added.text[:400]
    attachment = Attachment.query.filter_by(link_url=GOOD_URL).one()
    assert attachment.link_url == GOOD_URL

    edited = test_client.post(
        f'/event/{event.id}/manage/attachments/{attachment.folder_id}/{attachment.id}/',
        data={'title': 'Material renamed', 'link_url': GOOD_URL2, 'protected': '', 'folder': '', 'csrf_token': token},
    )
    db.session.expire_all()

    assert edited.status_code < 400, edited.text[:400]
    assert attachment.link_url == GOOD_URL2
    assert attachment.title == 'Material renamed'


def test_navigation_link_add_and_edit_keep_working(create_event, dummy_user, test_client, login, db):
    from indico.modules.events.layout.models.menu import MenuEntry

    event = _event(create_event)
    token = login(dummy_user)
    test_client.post(f'/event/{event.id}/manage/layout/menu/toggle-customize',
                     data={'enabled': '1', 'csrf_token': token})
    added = test_client.post(
        f'/event/{event.id}/manage/layout/menu/add?type=user_link',
        data={'title': 'Entry', 'link_url': GOOD_URL, 'is_enabled': 'y', 'csrf_token': token},
    )
    assert added.status_code < 400, added.text[:400]
    entry = MenuEntry.query.filter_by(link_url=GOOD_URL).one()

    edited = test_client.post(
        f'/event/{event.id}/manage/layout/menu/{entry.id}/',
        data={'title': 'Entry renamed', 'link_url': GOOD_URL2, 'is_enabled': 'y', 'csrf_token': token},
    )
    db.session.expire_all()

    assert edited.status_code < 400, edited.text[:400]
    assert entry.link_url == GOOD_URL2
    assert entry.title == 'Entry renamed'


def test_link_list_single_and_multiple_keep_working(create_event, dummy_user, test_client, login):
    from indico.modules.events.management.settings import privacy_settings

    event = _event(create_event)
    token = login(dummy_user)
    single = [{'title': '', 'url': GOOD_URL}]
    posted = test_client.post(
        f'/event/{event.id}/manage/privacy',
        data={'privacy_policy_urls': json.dumps(single), 'privacy_policy': '', 'csrf_token': token},
    )
    assert posted.status_code < 400, posted.text[:400]
    assert privacy_settings.get(event, 'privacy_policy_urls') == single

    multiple = [{'title': 'One', 'url': GOOD_URL}, {'title': 'Two', 'url': GOOD_URL2}]
    posted = test_client.post(
        f'/event/{event.id}/manage/privacy',
        data={'privacy_policy_urls': json.dumps(multiple), 'privacy_policy': '', 'csrf_token': token},
    )
    assert posted.status_code < 400, posted.text[:400]
    assert privacy_settings.get(event, 'privacy_policy_urls') == multiple


def test_event_map_link_keeps_working(create_event, dummy_user, test_client, login, db):
    event = _event(create_event)
    token = login(dummy_user)

    posted = test_client.post(
        f'/event/{event.id}/manage/settings/location',
        data={'own_map_url': GOOD_URL, 'location_data': LOCATION_DATA, 'csrf_token': token},
    )
    db.session.expire_all()

    assert posted.status_code < 400, posted.text[:400]
    assert event.own_map_url == GOOD_URL
    assert event.map_url == GOOD_URL


def test_event_website_link_keeps_working(create_event, dummy_user, test_client, login, db):
    from indico.modules.events.layout import layout_settings

    event = _event(create_event)
    token = login(dummy_user)
    posted = test_client.post(f'/event/{event.id}/manage/layout/',
                              data={'website_url': GOOD_URL, 'csrf_token': token})
    db.session.expire_all()

    assert posted.status_code < 400, posted.text[:400]
    assert layout_settings.get(event, 'website_url') == GOOD_URL
