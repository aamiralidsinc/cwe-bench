"""Seeing an image still works; protecting one only stops deletion."""

import json
import unittest

import harness.glanceworld as gw

PATCH_TYPE = 'application/openstack-images-v2.0-json-patch'


class TestLegitimateVisibilityAndUpdates(unittest.TestCase):

    def setUp(self):
        self.w = gw.get_world()
        self.w.reset_overrides()

    def test_public_image_is_readable_by_a_nonowner(self):
        image_id = self.w.create_image(owner='tenant-a', public=True)
        response = self.w.request('v2', 'GET', '/images/%s' % image_id,
                                  'tenant-b')
        self.assertEqual(200, response.status_int,
                         'a public image became unreadable: HTTP %s'
                         % response.status_int)
        self.assertEqual(image_id, json.loads(response.body)['id'])


    def test_protected_image_metadata_can_still_be_updated(self):
        image_id = self.w.create_image(owner='tenant-a', protected=True)
        body = json.dumps([{'replace': '/name', 'value': 'renamed'}])
        response = self.w.request('v2', 'PATCH', '/images/%s' % image_id,
                                  'tenant-a', body=body,
                                  content_type=PATCH_TYPE)
        self.assertEqual(200, response.status_int,
                         'updating a protected image failed: HTTP %s'
                         % response.status_int)
        row = self.w.meta(image_id)
        self.assertEqual('renamed', row['name'])
        self.assertTrue(row['protected'], 'the image stopped being protected')
        self.assertTrue(self.w.data_present(image_id))
