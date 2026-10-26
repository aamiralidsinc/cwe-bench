"""Behaviour tests: ordinary injection keeps working exactly as before."""
import json
import os
import unittest

from nova.virt.disk import api as disk_api

from harness import CANARY, Meta, PASSWD, SHADOW, Sandbox, password_fixtures


KEY = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ ' + CANARY
NET = 'auto lo\niface lo inet loopback\n'


class InjectionWorksTest(unittest.TestCase):
    def setUp(self):
        self.sandbox = Sandbox()
        self.sandbox.install()
        self.addCleanup(self.sandbox.remove)

    def read(self, *parts):
        f = open(self.sandbox.path(*parts), 'rb')
        try:
            return f.read()
        finally:
            f.close()

    def test_absolute_personality_path(self):
        disk_api.inject_files('image', [('/etc/motd', 'hello image')])
        self.assertEqual(self.read('etc', 'motd'), 'hello image')
        self.assertEqual(self.sandbox.writes_outside(), [])

    def test_relative_personality_path(self):
        disk_api.inject_files('image', [('var/lib/app/conf', 'setting=1')])
        self.assertEqual(self.read('var', 'lib', 'app', 'conf'),
                         'setting=1')

    def test_nested_personality_paths_are_created(self):
        disk_api.inject_files('image', [('/a/b/c/d/e/file', 'nested')])
        self.assertEqual(self.read('a', 'b', 'c', 'd', 'e', 'file'),
                         'nested')

    def test_personality_path_through_link_inside_image(self):
        os.makedirs(self.sandbox.path('etc'))
        self.sandbox.write(self.sandbox.path('etc', 'target'), 'before')
        self.sandbox.link('target', self.sandbox.path('etc', 'alias'))
        disk_api.inject_files('image', [('/etc/alias', 'after')])
        self.assertEqual(self.read('etc', 'target'), 'after')

    def test_ssh_key_is_appended_and_directories_prepared(self):
        os.makedirs(self.sandbox.path('root', '.ssh'))
        self.sandbox.write(self.sandbox.path('root', '.ssh',
                                             'authorized_keys'),
                           'existing-key\n')
        disk_api.inject_data('image', key=KEY)
        keys = self.read('root', '.ssh', 'authorized_keys')
        self.assertTrue(keys.startswith('existing-key\n'))
        self.assertIn(KEY, keys)
        keys2 = self.read('root', '.ssh', 'authorized_keys2')
        self.assertIn(KEY, keys2)
        mode = os.stat(self.sandbox.path('root', '.ssh')).st_mode & 0777
        self.assertEqual(mode, 0700)
        self.assertEqual(self.sandbox.writes_outside(), [])

    def test_ssh_key_through_link_inside_image(self):
        os.makedirs(self.sandbox.path('root', '.ssh'))
        self.sandbox.write(self.sandbox.path('root', '.ssh',
                                             'authorized_keys'), 'old\n')
        self.sandbox.link('authorized_keys',
                          self.sandbox.path('root', '.ssh',
                                            'authorized_keys2'))
        disk_api.inject_data('image', key=KEY)
        self.assertIn(KEY, self.read('root', '.ssh', 'authorized_keys'))
        self.assertEqual(self.sandbox.writes_outside(), [])

    def test_network_config_is_written(self):
        disk_api.inject_data('image', net=NET)
        self.assertEqual(self.read('etc', 'network', 'interfaces'), NET)
        mode = os.stat(self.sandbox.path('etc', 'network')).st_mode & 0777
        self.assertEqual(mode, 0755)
        self.assertEqual(self.sandbox.writes_outside(), [])

    def test_metadata_is_written(self):
        disk_api.inject_data('image',
                             metadata=[Meta('instance_id', CANARY)])
        data = json.loads(self.read('meta.js'))
        self.assertEqual(data, {'instance_id': CANARY})
        self.assertEqual(self.sandbox.writes_outside(), [])

    def test_admin_password_updates_only_root(self):
        password_fixtures(self.sandbox.path('etc'))
        disk_api.inject_data('image', admin_password='new-secret')
        shadow = self.read('etc', 'shadow')
        lines = dict(line.split(':', 1) for line in shadow.splitlines())
        old_root_hash = SHADOW.splitlines()[0].split(':')[1]
        new_root_hash = lines['root'].split(':', 1)[0]
        self.assertNotEqual(new_root_hash, old_root_hash)
        self.assertEqual(lines['nobody'],
                         SHADOW.splitlines()[1].split(':', 1)[1])
        self.assertEqual(self.read('etc', 'passwd'), PASSWD)
        self.assertEqual(self.sandbox.writes_outside(), [])

    def test_mounted_filesystem_entry_point(self):
        disk_api.inject_data_into_fs(self.sandbox.mnt, KEY, None, None,
                                     None, None)
        self.assertIn(KEY, self.read('root', '.ssh', 'authorized_keys'))
        self.assertEqual(self.sandbox.writes_outside(), [])


if __name__ == '__main__':
    unittest.main()
