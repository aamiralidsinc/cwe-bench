"""A protected image may not be deleted on the registry service's own route."""

import unittest

import harness.glanceworld as gw


class TestProtectedImageDeletion(unittest.TestCase):

    def setUp(self):
        self.w = gw.get_world()
        self.w.reset_overrides()

    def test_owner_cannot_delete_protected_image(self):
        image_id = self.w.create_image(owner='tenant-a', public=True,
                                       protected=True)
        response = self.w.request('registry', 'DELETE',
                                  '/images/%s' % image_id, 'tenant-a')
        gw.assert_client_error(self, response,
                               'registry delete of a protected image')
        self.assertTrue(self.w.image_live(image_id),
                        'the protected image metadata was destroyed')
        self.assertTrue(self.w.meta(image_id)['protected'])

    def test_admin_cannot_delete_protected_image(self):
        image_id = self.w.create_image(owner='tenant-a', public=True,
                                       protected=True)
        response = self.w.request('registry', 'DELETE',
                                  '/images/%s' % image_id, 'admin-tenant',
                                  admin=True)
        gw.assert_client_error(self, response,
                               'registry delete of a protected image by an admin')
        self.assertTrue(self.w.image_live(image_id),
                        'the protected image metadata was destroyed')

    def test_protected_image_survives_repeated_attempts(self):
        image_id = self.w.create_image(owner='tenant-a', public=True,
                                       protected=True)
        for tenant, admin in (('tenant-a', False), ('tenant-b', False),
                              ('admin-tenant', True)):
            self.w.request('registry', 'DELETE', '/images/%s' % image_id,
                           tenant, admin=admin)
        self.assertTrue(self.w.image_live(image_id),
                        'the protected image metadata was destroyed')
