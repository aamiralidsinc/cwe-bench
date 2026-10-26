"""Behaviour tests: nothing outside the mounted image may be created or changed.

Every case drives the public entry points the compute driver uses to put
material into a mounted instance image.  The sandbox stands in for the host;
a request that would reach outside the image must fail and must leave the
host side untouched.
"""
import os
import unittest

from nova.virt.disk import api as disk_api

from harness import (CANARY, Meta, PASSWD, SHADOW, Sandbox, password_fixtures)


KEY = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ ' + CANARY
NET = 'auto lo\niface lo inet loopback\n'


class EscapeTest(unittest.TestCase):
    def setUp(self):
        self.sandbox = Sandbox()
        self.sandbox.install()
        self.addCleanup(self.sandbox.remove)

    def refused(self, func, *args, **kwargs):
        before = self.sandbox.outside_snapshot()
        try:
            func(*args, **kwargs)
        except Exception:
            pass
        else:
            self.fail('the request was accepted instead of being refused')
        self.assertEqual(before, self.sandbox.outside_snapshot(),
                         'the refused request changed something outside the '
                         'image')

    def test_personality_parent_traversal_is_refused(self):
        self.refused(disk_api.inject_files, 'image',
                     [('../outside/escaped', 'owned')])
        self.assertFalse(os.path.exists(self.sandbox.outside_path('escaped')))

    def test_personality_symlinked_directory_is_refused(self):
        self.sandbox.link(self.sandbox.outside, self.sandbox.path('etc'))
        self.refused(disk_api.inject_files, 'image',
                     [('/etc/escaped', 'owned')])
        self.assertFalse(os.path.exists(self.sandbox.outside_path('escaped')))

    def test_personality_symlinked_file_is_refused(self):
        target = self.sandbox.outside_path('host-file')
        self.sandbox.write(target, 'original')
        self.sandbox.link(target, self.sandbox.path('motd'))
        self.refused(disk_api.inject_files, 'image',
                     [('/motd', 'owned')])
        self.assertEqual(open(target).read(), 'original')

    def test_personality_prefix_sibling_is_refused(self):
        # A path that shares the mount point's leading characters but is a
        # different directory must not be treated as inside it.
        self.refused(disk_api.inject_files, 'image',
                     [('../mnte/escaped', 'owned')])
        self.assertFalse(os.path.exists(os.path.join(self.sandbox.prefix,
                                                     'escaped')))

    def test_personality_directory_side_effect_is_refused(self):
        # The refusal must happen before the parent directory is created.
        self.refused(disk_api.inject_files, 'image',
                     [('../outside/newdir/escaped', 'owned')])
        self.assertFalse(os.path.isdir(self.sandbox.outside_path('newdir')))

    def test_ssh_key_symlinked_root_is_refused(self):
        self.sandbox.link(self.sandbox.outside, self.sandbox.path('root'))
        self.refused(disk_api.inject_data, 'image', key=KEY)
        self.assertFalse(os.path.exists(self.sandbox.outside_path('.ssh')))

    def test_ssh_key_symlinked_directory_is_refused(self):
        os.makedirs(self.sandbox.path('root'))
        self.sandbox.link(self.sandbox.outside,
                          self.sandbox.path('root', '.ssh'))
        self.refused(disk_api.inject_data, 'image', key=KEY)
        self.assertFalse(os.path.exists(self.sandbox.outside_path(
            'authorized_keys')))

    def test_ssh_key_second_key_file_is_refused(self):
        os.makedirs(self.sandbox.path('root', '.ssh'))
        target = self.sandbox.outside_path('host-keys')
        self.sandbox.write(target, 'original\n')
        self.sandbox.link(target,
                          self.sandbox.path('root', '.ssh',
                                            'authorized_keys2'))
        self.refused(disk_api.inject_data, 'image', key=KEY)
        self.assertEqual(open(target).read(), 'original\n')

    def test_network_config_symlinked_directory_is_refused(self):
        self.sandbox.link(self.sandbox.outside, self.sandbox.path('etc'))
        self.refused(disk_api.inject_data, 'image', net=NET)
        self.assertFalse(os.path.exists(self.sandbox.outside_path(
            'interfaces')))

    def test_metadata_symlinked_file_is_refused(self):
        target = self.sandbox.outside_path('host-meta')
        self.sandbox.write(target, 'original')
        self.sandbox.link(target, self.sandbox.path('meta.js'))
        self.refused(disk_api.inject_data, 'image',
                     metadata=[Meta('instance_id', CANARY)])
        self.assertEqual(open(target).read(), 'original')

    def test_password_symlinked_directory_is_refused(self):
        password_fixtures(self.sandbox.outside)
        self.sandbox.link(self.sandbox.outside, self.sandbox.path('etc'))
        before = open(self.sandbox.outside_path('shadow')).read()
        self.refused(disk_api.inject_data, 'image',
                     admin_password='new-secret')
        self.assertEqual(open(self.sandbox.outside_path('shadow')).read(),
                         before)

    def test_password_symlinked_passwd_file_is_refused(self):
        os.makedirs(self.sandbox.path('etc'))
        self.sandbox.write(self.sandbox.path('etc', 'shadow'), SHADOW)
        self.sandbox.write(self.sandbox.outside_path('passwd'), PASSWD)
        self.sandbox.link(self.sandbox.outside_path('passwd'),
                          self.sandbox.path('etc', 'passwd'))
        self.refused(disk_api.inject_data, 'image',
                     admin_password='new-secret')

    def test_password_symlinked_shadow_file_is_refused(self):
        os.makedirs(self.sandbox.path('etc'))
        self.sandbox.write(self.sandbox.path('etc', 'passwd'), PASSWD)
        self.sandbox.write(self.sandbox.outside_path('shadow'), SHADOW)
        self.sandbox.link(self.sandbox.outside_path('shadow'),
                          self.sandbox.path('etc', 'shadow'))
        before = open(self.sandbox.outside_path('shadow')).read()
        self.refused(disk_api.inject_data, 'image',
                     admin_password='new-secret')
        self.assertEqual(open(self.sandbox.outside_path('shadow')).read(),
                         before)


if __name__ == '__main__':
    unittest.main()
