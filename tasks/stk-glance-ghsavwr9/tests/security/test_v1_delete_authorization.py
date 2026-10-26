"""The v1 service must authorize a deletion before it touches stored data."""

import unittest

import harness.glanceworld as gw


class TestV1DeleteAuthorization(unittest.TestCase):

    def setUp(self):
        self.w = gw.get_world()
        self.w.reset_overrides()

    def test_nonowner_cannot_delete_public_image(self):
        image_id = self.w.create_image(owner='tenant-a', public=True)
        response = self.w.request('v1', 'DELETE', '/images/%s' % image_id,
                                  'tenant-b')
        gw.assert_client_error(self, response, 'v1 delete by a non-owner')
        self.assertTrue(self.w.data_present(image_id),
                        'the stored image data was removed')
        self.assertTrue(self.w.image_live(image_id),
                        'the image metadata was destroyed')
        self.assertEqual('active', self.w.meta(image_id)['status'])


    def test_nonowner_delete_is_not_queued_for_later(self):
        self.w.set_delayed_delete(True)
        image_id = self.w.create_image(owner='tenant-a', public=True)
        response = self.w.request('v1', 'DELETE', '/images/%s' % image_id,
                                  'tenant-b')
        gw.assert_client_error(self, response, 'v1 delayed delete by a non-owner')
        self.assertTrue(self.w.data_present(image_id),
                        'the stored image data was removed')
        self.assertFalse(self.w.queue_present(image_id),
                         'the deletion was queued even though it was refused')
        self.assertTrue(self.w.image_live(image_id))
        self.assertEqual('active', self.w.meta(image_id)['status'])
