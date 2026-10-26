"""Legitimate deletions keep working on every service and in every mode."""

import json
import unittest

import harness.glanceworld as gw

PATCH_TYPE = 'application/openstack-images-v2.0-json-patch'


class TestLegitimateDeletes(unittest.TestCase):

    def setUp(self):
        self.w = gw.get_world()
        self.w.reset_overrides()

    def test_v1_owner_deletes_own_image(self):
        image_id = self.w.create_image(owner='tenant-a')
        response = self.w.request('v1', 'DELETE', '/images/%s' % image_id,
                                  'tenant-a')
        self.assertTrue(200 <= response.status_int < 300,
                        'owner delete failed: HTTP %s' % response.status_int)
        self.assertFalse(self.w.data_present(image_id),
                         'the stored data was not removed')
        self.assertFalse(self.w.image_live(image_id))

    def test_v1_admin_deletes_another_users_image(self):
        image_id = self.w.create_image(owner='tenant-a', public=True)
        response = self.w.request('v1', 'DELETE', '/images/%s' % image_id,
                                  'admin-tenant', admin=True)
        self.assertTrue(200 <= response.status_int < 300,
                        'admin delete failed: HTTP %s' % response.status_int)
        self.assertFalse(self.w.data_present(image_id),
                         'the stored data was not removed')

    def test_v1_owner_delayed_delete_queues_and_keeps_data(self):
        self.w.set_delayed_delete(True)
        image_id = self.w.create_image(owner='tenant-a')
        response = self.w.request('v1', 'DELETE', '/images/%s' % image_id,
                                  'tenant-a')
        self.assertTrue(200 <= response.status_int < 300,
                        'owner delayed delete failed: HTTP %s'
                        % response.status_int)
        self.assertTrue(self.w.queue_present(image_id),
                        'the delayed deletion was not queued')
        self.assertTrue(self.w.data_present(image_id),
                        'the data was removed before the delayed deletion')
        self.assertEqual('pending_delete', self.w.meta(image_id)['status'])

    def test_v2_owner_deletes_own_image(self):
        image_id = self.w.create_image(owner='tenant-a')
        response = self.w.request('v2', 'DELETE', '/images/%s' % image_id,
                                  'tenant-a')
        self.assertTrue(200 <= response.status_int < 300,
                        'owner delete failed: HTTP %s' % response.status_int)
        self.assertFalse(self.w.data_present(image_id),
                         'the stored data was not removed')
        self.assertFalse(self.w.image_live(image_id))

    def test_v2_admin_deletes_another_users_image(self):
        image_id = self.w.create_image(owner='tenant-a', public=True)
        response = self.w.request('v2', 'DELETE', '/images/%s' % image_id,
                                  'admin-tenant', admin=True)
        self.assertTrue(200 <= response.status_int < 300,
                        'admin delete failed: HTTP %s' % response.status_int)
        self.assertFalse(self.w.data_present(image_id),
                         'the stored data was not removed')

    def test_v2_owner_unprotects_then_deletes(self):
        image_id = self.w.create_image(owner='tenant-a', protected=True)
        body = json.dumps([{'replace': '/protected', 'value': False}])
        response = self.w.request('v2', 'PATCH', '/images/%s' % image_id,
                                  'tenant-a', body=body,
                                  content_type=PATCH_TYPE)
        self.assertEqual(200, response.status_int,
                         'unprotecting a protected image failed: HTTP %s'
                         % response.status_int)
        response = self.w.request('v2', 'DELETE', '/images/%s' % image_id,
                                  'tenant-a')
        self.assertTrue(200 <= response.status_int < 300,
                        'delete after unprotect failed: HTTP %s'
                        % response.status_int)
        self.assertFalse(self.w.data_present(image_id),
                         'the stored data was not removed')

    def test_owner_deletes_queued_image_without_stored_data(self):
        image_id = self.w.create_image(owner='tenant-a', with_data=False,
                                       status='queued')
        response = self.w.request('v2', 'DELETE', '/images/%s' % image_id,
                                  'tenant-a')
        self.assertTrue(200 <= response.status_int < 300,
                        'delete of a queued image failed: HTTP %s'
                        % response.status_int)
        self.assertFalse(self.w.image_live(image_id))
